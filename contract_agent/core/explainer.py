from __future__ import annotations

from collections import defaultdict
from typing import Any

from contract_agent.core.models import ContractIssue, ContractReport


def explain_report(report: ContractReport) -> dict[str, Any]:
    issues = report.issues
    return {
        "dataset": report.source,
        "status": status_label(report.status),
        "summary": summary(report),
        "problems": explain_problems(issues),
        "probableCauses": probable_causes(issues),
        "impacts": impacts(issues),
        "correctionPlan": correction_plan(issues),
    }


def status_label(status: str) -> str:
    return {
        "PASS": "Succès",
        "WARN": "Avertissement",
        "FAIL": "Échec",
    }.get(status, status)


def summary(report: ContractReport) -> str:
    counts = report.as_dict()["counts"]
    if report.status == "PASS":
        return "Les données reçues respectent le contrat attendu."
    return (
        f"L'agent a détecté {counts['FAIL']} problème(s) bloquant(s) "
        f"et {counts['WARN']} avertissement(s) sur `{report.source}`."
    )


def explain_problems(issues: list[ContractIssue]) -> list[str]:
    grouped: dict[tuple[str, str, str], list[ContractIssue]] = defaultdict(list)
    for issue in issues:
        grouped[(issue.check, issue.column, str(issue.expected))].append(issue)

    problems: list[str] = []
    for (check, column, _), group in grouped.items():
        first = group[0]
        count = len(group)
        if check == "column.renamed":
            problems.append(
                f'La colonne obligatoire "{column}" est absente. Une colonne similaire "{first.actual}" est présente.'
            )
        elif check == "column.missing":
            problems.append(f'La colonne attendue "{column}" est absente du fichier reçu.')
        elif check == "column.extra":
            problems.append(f'La colonne inconnue "{column}" est présente sans être déclarée dans le contrat.')
        elif check == "type.change":
            problems.append(f'Le type de "{column}" a changé : attendu `{first.expected}`, reçu `{first.actual}`.')
        elif check == "value.required":
            problems.append(f'{count_label(first.actual, count)} valeur(s) nulles ont été détectées dans la colonne obligatoire "{column}".')
        elif check == "value.format":
            problems.append(
                f'"{column}" contient {count} valeur(s) avec un format invalide. '
                f"Format attendu : `{first.expected}`. Exemple reçu : `{first.actual}`."
            )
        elif check == "value.type":
            problems.append(
                f'"{column}" contient {count} valeur(s) non convertibles en `{first.expected}`. '
                f"Exemple reçu : `{first.actual}`."
            )
        elif check == "value.pattern":
            problems.append(f'"{column}" contient {count} valeur(s) qui ne respectent pas le pattern attendu.')
        elif check == "value.min":
            problems.append(f'"{column}" contient {count} valeur(s) inférieure(s) au minimum attendu `{bound_label(first.expected)}`.')
        elif check == "value.max":
            problems.append(f'"{column}" contient {count} valeur(s) supérieure(s) au maximum attendu `{bound_label(first.expected)}`.')
        else:
            problems.append(f"{first.message} Colonne : `{column}`.")
    return problems


def probable_causes(issues: list[ContractIssue]) -> list[str]:
    causes: list[str] = []
    for issue in issues:
        if issue.check == "column.renamed":
            causes.append(
                f'Il est probable que le producteur ait renommé "{issue.expected}" en "{issue.actual}".'
            )
        elif issue.check == "value.format":
            causes.append(f'Le producteur a probablement changé le format de "{issue.column}" sans versionner le contrat.')
        elif issue.check == "value.min":
            causes.append(f'La règle métier de positivité sur "{issue.column}" n\'est pas appliquée en amont.')
        elif issue.check == "value.required":
            causes.append(f'Le producteur envoie des lignes incomplètes pour la clé ou le champ obligatoire "{issue.column}".')
        elif issue.check == "type.change":
            causes.append(f'Le typage de "{issue.column}" a dérivé entre la source et le contrat.')
    return dedupe(causes)


def impacts(issues: list[ContractIssue]) -> list[str]:
    checks = {issue.check for issue in issues}
    columns = {issue.column.lower() for issue in issues}
    result: list[str] = []

    if "column.renamed" in checks:
        result.append("Risque de rupture de mapping : les jobs aval peuvent lire des valeurs nulles ou échouer.")
    if "column.missing" in checks:
        result.append("Risque d'échec des traitements qui dépendent de colonnes obligatoires.")
    if "type.change" in checks:
        result.append("Risque de cast incorrect ou d'échec lors de l'écriture vers Spark, warehouse ou Iceberg.")
    if "value.format" in checks:
        result.append("Risque d'erreur de parsing ou d'inversion jour/mois sur les dates.")
    if "value.type" in checks:
        result.append("Risque de rejet des lignes ou de valeurs invalides après casting.")
    if checks & {"value.min", "value.max"}:
        result.append("Risque d'indicateurs métier faux à cause de valeurs hors bornes.")
    if "value.required" in checks:
        result.append("Risque de clés nulles, de mauvaises jointures et de métriques incomplètes.")
    if checks & {"column.missing", "column.renamed", "type.change", "value.type", "value.format"}:
        result.append("Risque d'échec du pipeline Spark ou de l'append Iceberg.")
    if "customer_id" in columns:
        result.append("Risque de mauvaise jointure sur `customer_id` et de métriques client incomplètes.")
    if "amount" in columns:
        result.append("Risque qualité sur les dashboards finance et les agrégats de montant.")
    if "email" in columns or "mail" in columns:
        result.append("Risque que les contrôles RGPD/PII ne s'appliquent plus au bon champ.")
    return dedupe(result)


def correction_plan(issues: list[ContractIssue]) -> list[str]:
    plan: list[str] = []
    for issue in issues:
        if issue.check == "column.renamed":
            plan.append(f'Renommer "{issue.actual}" en "{issue.expected}" ou mettre à jour le contrat si le changement est volontaire.')
        elif issue.check == "column.missing":
            plan.append(f'Ajouter "{issue.column}" dans le fichier source ou rendre la colonne optionnelle dans le contrat.')
        elif issue.check == "type.change":
            plan.append(f'Caster "{issue.column}" en `{issue.expected}` avant publication.')
        elif issue.check == "value.required":
            plan.append(f'Rejeter ou mettre en quarantaine les lignes où "{issue.column}" est vide.')
        elif issue.check == "value.format":
            plan.append(f'Convertir "{issue.column}" au format `{issue.expected}` avant ingestion.')
        elif issue.check == "value.type":
            plan.append(f'Nettoyer ou caster "{issue.column}" pour garantir le type `{issue.expected}`.')
        elif issue.check == "value.min":
            plan.append(f'Appliquer une règle `min` sur "{issue.column}" et rejeter les valeurs sous `{bound_label(issue.expected)}`.')
        elif issue.check == "value.max":
            plan.append(f'Appliquer une règle `max` sur "{issue.column}" et rejeter les valeurs au-dessus de `{bound_label(issue.expected)}`.')
        elif issue.check == "column.extra":
            plan.append(f'Ajouter "{issue.column}" au contrat seulement si ce champ est volontaire.')
    return dedupe(plan)


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def count_label(value: Any, fallback: int) -> str:
    if value is None:
        return str(fallback)
    text = str(value).strip()
    first = text.split(" ", 1)[0]
    return first if first.isdigit() else str(fallback)


def bound_label(value: Any) -> str:
    text = str(value or "").strip()
    for prefix in (">= ", "<= "):
        if text.startswith(prefix):
            return text[len(prefix) :]
    return text
