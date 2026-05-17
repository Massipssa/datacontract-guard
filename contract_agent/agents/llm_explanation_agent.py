from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from contract_agent.agents.base import AgentStep, ok_step


LLMProvider = Callable[[dict[str, Any]], dict[str, Any]]

try:
    from contract_agent.agents.document_retriever import DocumentRetriever  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    DocumentRetriever = None


@dataclass(frozen=True)
class LLMExplanation:
    status: str
    status_source: str
    explanation: str
    business_impact: str
    proposed_correction: str
    supplier_message: str
    generated_by: str

    def as_dict(self) -> dict[str, str]:
        return {
            "status": self.status,
            "statusSource": self.status_source,
            "explanation": self.explanation,
            "businessImpact": self.business_impact,
            "proposedCorrection": self.proposed_correction,
            "supplierMessage": self.supplier_message,
            "generatedBy": self.generated_by,
        }


@dataclass(frozen=True)
class LLMExplanationResult:
    explanation: LLMExplanation
    step: AgentStep


class LLMExplanationAgent:
    name = "LLM Explanation Agent"

    def __init__(self, provider: LLMProvider | None = None, retriever: "DocumentRetriever" | None = None) -> None:
        self.provider = provider
        self.retriever = retriever

    def generate(self, report_payload: dict[str, Any]) -> LLMExplanationResult:
        engine_status = str(report_payload.get("status") or "UNKNOWN")
        # attempt to retrieve reference documents if a retriever is configured
        reference_docs: list[dict[str, Any]] = []
        try:
            if self.retriever is not None:
                query_parts = []
                analysis = report_payload.get("analysis") or {}
                if isinstance(analysis.get("problems"), list):
                    query_parts.extend([str(x) for x in analysis.get("problems")])
                if isinstance(analysis.get("correctionPlan"), list):
                    query_parts.extend([str(x) for x in analysis.get("correctionPlan")])
                query = "\n".join(query_parts) or "data contract guidelines"
                reference_docs = self.retriever.search(query, top_k=3) if hasattr(self.retriever, "search") else []
        except Exception:
            reference_docs = []

        llm_payload = self.prompt_payload(report_payload, reference_docs)
        if self.provider is None:
            explanation = fallback_explanation(report_payload, engine_status, reference_docs)
        else:
            explanation = self.from_provider(self.provider(llm_payload), report_payload, engine_status)

        step = ok_step(
            self.name,
            "Clear explanation, business impact, correction, and supplier message generated.",
            status=engine_status,
            statusSource="validation_engine",
            generatedBy=explanation.generated_by,
        )
        return LLMExplanationResult(explanation=explanation, step=step)

    def prompt_payload(self, report_payload: dict[str, Any], reference_docs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        payload = {
            "instruction": (
                "Explain the validation report for data engineers. "
                "Generate explanation, business impact, proposed correction, and supplier message. "
                "Never change the PASS/FAIL status; it is owned by the validation engine."
            ),
            "validationReport": report_payload,
            "requiredOutput": {
                "explanation": "clear diagnosis",
                "businessImpact": "business and pipeline risk",
                "proposedCorrection": "actionable remediation",
                "supplierMessage": "short message to send to the data producer",
            },
        }
        if reference_docs:
            # Provide short reference documents to the LLM for contextual enrichment
            payload["referenceDocuments"] = [
                {"source": doc.get("source"), "text": (doc.get("text") or "").strip()[:1000]} for doc in reference_docs
            ]
        return payload

    def from_provider(
        self,
        provider_payload: dict[str, Any],
        report_payload: dict[str, Any],
        engine_status: str,
    ) -> LLMExplanation:
        fallback = fallback_explanation(report_payload, engine_status)
        return LLMExplanation(
            status=engine_status,
            status_source="validation_engine",
            explanation=clean_text(provider_payload.get("explanation")) or fallback.explanation,
            business_impact=clean_text(provider_payload.get("businessImpact")) or fallback.business_impact,
            proposed_correction=clean_text(provider_payload.get("proposedCorrection")) or fallback.proposed_correction,
            supplier_message=clean_text(provider_payload.get("supplierMessage")) or fallback.supplier_message,
            generated_by="llm_provider",
        )


def fallback_explanation(report_payload: dict[str, Any], engine_status: str, reference_docs: list[dict[str, Any]] | None = None) -> LLMExplanation:
    analysis = report_payload.get("analysis") or {}
    source = str(report_payload.get("source") or analysis.get("dataset") or "dataset")
    problems = as_text_list(analysis.get("problems"))
    impacts = as_text_list(analysis.get("impacts"))
    corrections = as_text_list(
        analysis.get("correctionPlan")
        or report_payload.get("recommendations")
        or [item.get("suggestion") for item in report_payload.get("corrections", []) if isinstance(item, dict)]
    )

    if engine_status == "PASS":
        explanation = f"`{source}` respecte le contrat attendu. Aucun écart bloquant n'a été détecté."
        business_impact = "Le pipeline peut continuer avec un risque qualité faible sur les règles vérifiées."
        proposed_correction = "Aucune correction nécessaire. Conserver le contrat et les contrôles en CI/CD."
        supplier_message = (
            f"Bonjour, le fichier `{source}` est conforme au contrat de données. "
            "Vous pouvez poursuivre la livraison."
        )
        # add references when available
        if reference_docs:
            refs = "\n".join(f"Réf: {d.get('source')}" for d in reference_docs)
            explanation = explanation + "\n\n" + refs
    else:
        explanation = join_sentences(
            problems,
            default=f"`{source}` ne respecte pas le contrat de données attendu.",
        )
        business_impact = join_sentences(
            impacts,
            default="Le pipeline d'ingestion, les tables analytiques ou les contrôles métier peuvent être impactés.",
        )
        proposed_correction = join_sentences(
            corrections,
            default="Corriger les écarts détectés ou versionner explicitement le contrat si le changement est volontaire.",
        )
        supplier_message = supplier_message_for(source, problems, corrections)

    # include short reference excerpts when available
    if reference_docs and engine_status != "PASS":
        excerpts = []
        for d in reference_docs[:3]:
            text = (d.get("text") or "").strip()
            if text:
                excerpts.append(f"({d.get('source')}) {text[:400].rstrip()}")
        if excerpts:
            explanation = explanation + "\n\nRéférences :\n" + "\n---\n".join(excerpts)

    return LLMExplanation(
        status=engine_status,
        status_source="validation_engine",
        explanation=explanation,
        business_impact=business_impact,
        proposed_correction=proposed_correction,
        supplier_message=supplier_message,
        generated_by="deterministic_fallback",
    )


def supplier_message_for(source: str, problems: list[str], corrections: list[str]) -> str:
    top_problems = numbered(problems[:3]) if problems else "1. des écarts avec le contrat attendu"
    top_corrections = numbered(corrections[:3]) if corrections else "1. corriger ou versionner le contrat"
    return (
        f"Bonjour,\n\n"
        f"DataContract Guard a bloqué `{source}` car le fichier ne respecte pas le contrat attendu.\n\n"
        f"Problèmes détectés :\n{top_problems}\n\n"
        f"Corrections attendues :\n{top_corrections}\n\n"
        f"Merci de renvoyer un fichier corrigé ou de confirmer un changement volontaire du contrat."
    )


def as_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def join_sentences(items: list[str], default: str) -> str:
    if not items:
        return default
    return " ".join(item.rstrip(".") + "." for item in items)


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def numbered(items: list[str]) -> str:
    return "\n".join(f"{index}. {item.rstrip('.')}" for index, item in enumerate(items, start=1))
