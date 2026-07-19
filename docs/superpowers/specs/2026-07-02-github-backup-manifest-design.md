# GitHub Backup Manifest Design

## Goal

Make GitHub sync more backup-like by writing a small manifest with each sync commit.

## Scope

This slice adds metadata only. It does not upload `embeddings.db`, change bucket markdown paths, create releases, or alter restore overwrite semantics.

## Design

`GitHubSync` builds `_ombre_backup_manifest.json` under the configured `path_prefix`. The manifest contains:

- schema version
- generation timestamp
- repo branch/path prefix
- file count and total bytes
- one entry per bucket markdown with relative path, byte size, and sha256

The manifest is committed in the same tree as the markdown files. `_batch_commit()` continues returning the number of markdown files uploaded, so existing Dashboard copy remains accurate.

`import_from_github()` reads the manifest when present and returns a compact `backup_manifest` summary with file count, total bytes, generated timestamp, and whether the manifest file was present.

## Testing

Add tests that verify manifest hashing, manifest inclusion in the Git tree payload, and optional manifest readback during import.

