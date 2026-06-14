Temporary dev/fast-iteration scripts with no long-term value.
Overlaps with pose-guided-video-generation skill where MimicMotion deployment
details are maintained. Keeping this skill for the broader scope (pose analysis
pipelines, biomechanical metrics) but the video-gen aspect lives in the
dedicated skill. If the user asks about MimicMotion specifically, load
pose-guided-video-generation which has the richer reference.
