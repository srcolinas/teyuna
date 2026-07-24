# teyuna-core

Shared game types and constants used by the Teyuna backend and Python SDK.

Includes public ports DTOs, player action/result models, board geometry helpers
needed by those models, and Final-typed game constants.

## Publishing

Publish **`teyuna-core` before `teyuna-sdk`**, because the SDK depends on this
package on PyPI.

```bash
make publish
```
