# Data Contract Report: customer_profile_contract

- Source: `source_sample`
- Status: `FAIL`
- Failures: `1`
- Warnings: `3`

## Issues

- **FAIL** `column.missing` on `signup_ts`: Column declared in the contract is missing from the source schema.
  - expected: `timestamp`
  - actual: `None`
- **WARN** `column.missing` on `country`: Column declared in the contract is missing from the source schema.
  - expected: `string`
  - actual: `None`
- **WARN** `column.extra` on `created_at`: Source column is not declared in the contract.
  - expected: `None`
  - actual: `string`
- **WARN** `column.extra` on `marketing_opt_in`: Source column is not declared in the contract.
  - expected: `None`
  - actual: `boolean`

## Proposed Corrections

- `ADD_SOURCE_COLUMN` on `signup_ts`: Add `signup_ts` as `timestamp` in the source pipeline or mark it optional in the contract.
- `ADD_SOURCE_COLUMN` on `country`: Add `country` as `string` in the source pipeline or mark it optional in the contract.
- `ADD_CONTRACT_COLUMN` on `created_at`: Add `created_at` as `string` to the contract if this new field is intentional.
- `ADD_CONTRACT_COLUMN` on `marketing_opt_in`: Add `marketing_opt_in` as `boolean` to the contract if this new field is intentional.
# Data Contract Report: customer_profile_contract

- Source: `source_sample`
- Status: `FAIL`
- Failures: `1`
- Warnings: `3`

## Issues

- **FAIL** `column.missing` on `signup_ts`: Column declared in the contract is missing from the source schema.
  - expected: `timestamp`
  - actual: `None`
- **WARN** `column.missing` on `country`: Column declared in the contract is missing from the source schema.
  - expected: `string`
  - actual: `None`
- **WARN** `column.extra` on `created_at`: Source column is not declared in the contract.
  - expected: `None`
  - actual: `string`
- **WARN** `column.extra` on `marketing_opt_in`: Source column is not declared in the contract.
  - expected: `None`
  - actual: `boolean`

## Proposed Corrections

- `ADD_SOURCE_COLUMN` on `signup_ts`: Add `signup_ts` as `timestamp` in the source pipeline or mark it optional in the contract.
- `ADD_SOURCE_COLUMN` on `country`: Add `country` as `string` in the source pipeline or mark it optional in the contract.
- `ADD_CONTRACT_COLUMN` on `created_at`: Add `created_at` as `string` to the contract if this new field is intentional.
- `ADD_CONTRACT_COLUMN` on `marketing_opt_in`: Add `marketing_opt_in` as `boolean` to the contract if this new field is intentional.
