# Ch22 - YOLO 항상, DETR+SR은 헷갈릴 때만

YOLO_MS = 33
SR_MS = 45
DETR_MS = 215
POSE_MS = 8
FLOW_MS = 12
TARGET_MS = 50  # 20 FPS

def should_enhance(conf: float) -> str:
    if conf >= 0.85:
        return 'track'
    if conf >= 0.5:
        return 'enhance'
    return 'ignore'

def calculate_iou(box1, box2):
    # [x,y,w,h]
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    xi1, yi1 = max(x1,x2), max(y1,y2)
    xi2, yi2 = min(x1+w1,x2+w2), min(y1+h1,y2+h2)
    inter = max(0, xi2-xi1) * max(0, yi2-yi1)
    union = w1*h1 + w2*h2 - inter
    return inter / union if union > 0 else 0

def merge_boxes(b1, b2):
    return [(a+b)/2 for a,b in zip(b1,b2)]

def fuse_detections(thermal_dets, visible_dets, iou_threshold=0.3):
    fused = []
    for t in thermal_dets:
        best, best_iou = None, 0
        for v in visible_dets:
            iou = calculate_iou(t['bbox'], v['bbox'])
            if iou > best_iou:
                best_iou, best = iou, v
        if best and best_iou > iou_threshold:
            fused.append({
                'bbox': merge_boxes(t['bbox'], best['bbox']),
                'combined_conf': (t['confidence'] + best['confidence'])/2,
                'source': 'both'
            })
        else:
            fused.append({**t, 'source': 'thermal'})
    for v in visible_dets:
        if not any(calculate_iou(v['bbox'], f['bbox']) > iou_threshold for f in fused):
            fused.append({**v, 'source': 'visible'})
    return fused

def estimate_pipeline_ms(detections):
    # worst-case 합산
    t = YOLO_MS
    for d in detections:
        action = should_enhance(d['confidence'])
        if action == 'enhance':
            t += SR_MS + DETR_MS
        if d['confidence'] > 0.85:
            t += POSE_MS + FLOW_MS
    return t

def can_run_full_pipeline(detections):
    return estimate_pipeline_ms(detections) <= 300
