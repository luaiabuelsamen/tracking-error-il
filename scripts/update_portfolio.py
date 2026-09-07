"""Build a portable gallery from existing recordings; never operates the robot."""
import json
import shutil
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
media=ROOT/'research/portfolio/media'; media.mkdir(parents=True,exist_ok=True)
items=[]
def add(source,name,title,kind,description):
    source=ROOT/source
    if not source.exists():return
    dest=media/name
    shutil.copy2(source,dest)
    poster=dest.with_suffix('.jpg')
    subprocess.run(['ffmpeg','-v','error','-y','-ss','1','-i',str(dest),'-frames:v','1',str(poster)],check=True,capture_output=True)
    items.append(dict(src='media/'+name,poster='media/'+poster.name,title=title,type=kind,description=description))
showcase = sorted((ROOT/'results/showcase').glob('*.mp4'), reverse=True)
if showcase:
    source = showcase[0]
    add(source,source.name,'Tracking error · physical rollout','Hardware policy','Selected seed-1 checkpoint. Autonomous control after a fixed demonstration replay. Showcase recording; outcome has not been annotated and this run is not included in the evaluation counts.')
add(Path('data/real/pickplace_real_v0/clips/episode_000.mp4'),'teleoperation.mp4','The task, demonstrated','Teleoperation','A human-controlled SO-101 picks up an adapter and places it inside a tape roll. This is a training demonstration, not autonomous policy performance.')
add(Path('delta_policy_demo.mp4'),'simulation_delta.mp4','Tracking error in simulation','Simulation','A simulated ACT policy with tracking-error observations. Rendered forces describe the simulator, not measurements from the physical robot.')
shutil.copy2(ROOT/'paper/main.pdf',media/'paper.pdf')
(ROOT/'research/portfolio/gallery.js').write_text('window.robotGallery = '+json.dumps(items,indent=2)+';\n')
print(f'Gallery updated: {len(items)} recordings. Open research/portfolio/index.html or serve research/portfolio/.')
