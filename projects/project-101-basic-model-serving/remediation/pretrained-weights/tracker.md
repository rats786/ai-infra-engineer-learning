# Pretrained Weights Learning Tracker

This tracker guides the move from a randomly initialized ResNet to a useful pretrained ImageNet classifier.

## Mental Model

- **Architecture:** the ResNet layer layout and operations.
- **Weights:** learned numeric parameters downloaded and loaded into that architecture.
- **Preprocessing:** image resizing and normalization expected by the weight set.
- **Classes:** human-readable labels corresponding to the model's 1,000 outputs.
- **Inference:** passing an image through loaded weights without changing or training them.

## Work Items

| ID | Status | Learning outcome | Change |
| --- | --- | --- | --- |
| PW-1 | Complete | Select compatible official pretrained weights for ResNet-18/ResNet-50. | `src/model.py` now selects each model's `DEFAULT` weight enum. |
| PW-2 | Complete | Understand why preprocessing and labels must match the weights. | The model now uses the weight set's `transforms()` and category metadata. |
| PW-3 | Pending | Observe first-run and cached weight loading. | Run a model load locally and record cache/download behavior. |
| PW-4 | Pending | Verify meaningful predictions with a known image. | Test `/predict` with clearly recognizable example images. |
| PW-5 | Pending | Handle offline/container deployment deliberately. | Decide between a persistent Torch cache or approved packaged model artifacts. |
| PW-6 | Pending | Add fine-tuning only after pretrained inference is understood. | Train custom classes with a small labeled dataset and save the resulting weights. |

## What Happens Now

Calling `load_model()` selects `ResNet18_Weights.DEFAULT` (or the ResNet-50 equivalent). Torchvision downloads the official weight file on the first load when it is not already cached, then loads those values into the model. Later loads normally reuse the local cache.

The application still runs in inference mode with gradients disabled. It does not train or modify the pretrained weights during API requests.

## Validation

Run the focused model tests:

```bash
pytest tests/test_model.py -q --no-cov
```

Use `--no-cov` for this focused learning check; the repository-wide coverage target is intended for the full test suite.

Then start the API and send a recognizable JPEG or PNG to `/predict`. Confidence values are probabilities from the model output, not guarantees of correctness. The current project does not support custom classes until fine-tuning and class-label changes are implemented.

## Notes

- Do not commit downloaded `.pth` cache files; Docker/runtime artifacts belong outside source control.
- A first model load requires network access unless the matching weights are already cached or packaged.
- For predictable production startup, validate or package weights during an approved build/deployment step rather than relying on a live download during scaling.
