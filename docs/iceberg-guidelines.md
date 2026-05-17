# Iceberg Guidelines

Guidelines for writing data into Iceberg tables:

- Use explicit schema evolution and versioning for breaking changes.
- Avoid silent column renames; prefer adding a new column and deprecating the old one.
- Validate partitioning and primary keys to avoid append-time failures.
