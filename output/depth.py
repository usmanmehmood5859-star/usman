import onnxruntime as ort, numpy as np, cv2, sys
IMG='/tmp/claude-0/-home-user-usman/17155274-85b6-5c26-9ac5-e4d3e2acc502/images'
s=ort.InferenceSession('dav2.onnx',providers=['CPUExecutionProvider'])
inp=s.get_inputs()[0].name
for k in range(1,6):
    im=cv2.cvtColor(cv2.imread(f'{IMG}/{k}.webp'),cv2.COLOR_BGR2RGB)
    h,w=im.shape[:2]; sc=518/max(h,w); nh,nw=int(round(h*sc/14)*14),int(round(w*sc/14)*14)
    x=cv2.resize(im,(nw*2,nh*2),interpolation=cv2.INTER_CUBIC).astype(np.float32)/255  # 2x for detail
    x=(x-[0.485,0.456,0.406])/[0.229,0.224,0.225]
    d=s.run(None,{inp:x.transpose(2,0,1)[None].astype(np.float32)})[0][0]
    d=cv2.resize(d,(w,h),interpolation=cv2.INTER_CUBIC)
    d=(d-np.percentile(d,1))/(np.percentile(d,99)-np.percentile(d,1)); d=np.clip(d,0,1)
    np.save(f'd{k}.npy',d.astype(np.float32))
    cv2.imwrite(f'd{k}.png',cv2.resize((d*255).astype(np.uint8),(w//4,h//4)))
    print(k,d.shape)
