# SO-ARM100 / SO-101 model assets

`so_arm100.xml` and the STL meshes under `assets/` derive from the
`trs_so_arm100` model in [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie)
(Google DeepMind), itself built from the SO-ARM100 CAD released by
[TheRobotStudio](https://github.com/TheRobotStudio/SO-ARM100). Both are
distributed under the Apache License 2.0; the meshes are used here under that
license and remain the work of their original authors.

Local modifications:

- elliptic friction cone with `impratio="10"`, so a grasped object does not
  slide out of the fingers;
- explicit thin-box finger pads on the fixed and moving jaws;
- collision geometry separated from the visual meshes;
- `scene.xml`, which adds the table, block, and container used by the task.
