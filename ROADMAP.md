# Roadmap

## Ideas

- Integrate a Dockerfile parser so users can "pythainerize" existing projects.
  The tool would parse a Dockerfile into an AST (existing Python packages?),
  translate that AST into Pythainer builder commands, and then emit a starter
  Python script. Users could subsequently factor features into independent
  builders.

- Convert shell history into a Pythainer script. During prototyping, developers
  often focus on getting the configuration right and postpone automation. Once
  the system works, automatic provisioning becomes a priority. Provide a tool
  that ingests shell history and generates the corresponding Pythainer builder
  steps as a starting point for cleanup and composition.

## Planned builders

- CUDA builder
- ROS 2 builder

## Chore

- Move license to VUB.
