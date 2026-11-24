# Orange-and-white kitten desk poses

`python scripts/build-kitten-reference.py` extracts the approved `face-reference.png` into `reference-body.webp`. `python scripts/build-kitten-desk-poses.py` builds the three upright body plates and the left keyboard foreleg. The plates use 600 portrait units plus 100 units of left margin (138 for the extended mouse grip). All share the same head correction, chest shortening, and desk baseline.

The grip uses the continuous shoulder and foreleg from `mouse-pose-master.webp`, blended into the reference inside the chest. Its contact point is (-77, 579) in body coordinates. At runtime this point rests on the inner half of the mouse. Keyboard poses use a foreleg sampled from that master with a fixed shoulder pivot and rigid toes.

`python scripts/build-kitten-poses.py` rebuilds `native-forepaws.webp` from the lossless right foreleg master. The live desk poses use the photographic foreleg for both mouse and key contacts. Shoulder roots are (101, 363) and (456, 441) at the marked flanks; relaxed toes are (106, 568) and (385, 568).
