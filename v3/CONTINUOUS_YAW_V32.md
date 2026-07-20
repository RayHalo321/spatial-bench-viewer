# Continuous Yaw v3.2

This extension evaluates camera-relative continuous yaw from final RGB images only. It does not read Blender coordinates, MUSES scene rotations, asset front-axis metadata, or method identity.

## Targets

| Target | Visual bin | Accepted visual interval |
|---|---|---|
| 30 degrees | `slight` | 15-45 degrees |
| 60 degrees | `diagonal` | 45-75 degrees |
| 90 degrees | `side` | 75-105 degrees |

Do not mix 30 and 45 degrees in the same benchmark. Left/right-only prompts remain diagnostic and do not enter the continuous-yaw main score.

## Core Relation

```json
{
  "id": "r1",
  "type": "face_angle",
  "subject": "television_1",
  "primary": true,
  "frame": "image",
  "angle_reference": "facing_viewer",
  "direction": "right",
  "angle_degrees": 30,
  "tolerance_deg": 15,
  "facing_part": "screen_side"
}
```

`face_angle` is the runtime-facing schema for a named front part that starts by facing the viewer and then turns in image coordinates. `rotate_yaw` remains reserved for absolute Blender/world yaw. The expected visual bin is derived from `angle_degrees`; it is not duplicated in the core truth.

## VLM Input

Every method receives the same judge input:

1. complete final RGB image;
2. subject crop localized from that RGB image;
3. fixed yaw-bin reference card;
4. prompt, subject mention, and named functional front part.

The judge returns subject visibility, front-part visibility, turn direction, and yaw bin. `unclear`, missing output, or an unreadable named part scores zero.

## Metrics

- `Yaw Direction Accuracy`
- `Yaw Magnitude-bin Accuracy`
- `Yaw Joint Accuracy`

Direction and magnitude are gated by subject and named-front readability. Joint passes only when both gated checks pass. No 3D yaw metric is reported.

Run `scripts/evaluate_continuous_yaw_vlm.py` for evaluation. Qwen3-VL-32B may provide the first-pass labels; unclear or disputed cases should be retained for later visual adjudication rather than converted into partial credit.
