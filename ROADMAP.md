# Roadmap

## Ideas

- Integrate a Dockerfile parser so users can "pythainerize" existing projects.
  The tool would parse a Dockerfile into an AST (existing Python packages?),
  translate that AST into Pythainer builder commands, and then emit a starter
  Python script. Users could subsequently factor features into independent
  builders. A first version can support a documented subset of Dockerfile
  constructs and report the unsupported ones explicitly.

- Convert shell history into a Pythainer script. During prototyping, developers
  often focus on getting the configuration right and postpone automation. Once
  the system works, automatic provisioning becomes a priority. Provide a tool
  that ingests shell history and generates the corresponding Pythainer builder
  steps as a starting point for cleanup and composition. Shell history alone
  cannot establish a complete environment: the outcome is a draft to review,
  with missing inputs and ambiguous steps marked.

- Standard entry points for build scripts. Most Pythainer scripts end up
  re-implementing the same small command line (build, run, open a shell in
  the container without rebuilding). Provide a helper that gives a script
  these subcommands from its builder and runner.

## Refactoring: Dockerfile AST

- Represent Dockerfile instructions as typed command objects (an AST) instead
  of raw strings. Today most builder methods append a `StrDockerBuildCommand`,
  so anything that needs to reason about the instructions has to parse strings
  back. The squash stage is the first victim: it extracts `ARG`, `ENV`,
  `WORKDIR` and `USER` by string matching, and renames the first stage by
  patching the `FROM` line (see the TODO in `_generate_squash_suffix`).
- What the AST unlocks, each as a separate step once the representation
  exists:
  - Squash rewritten on typed commands, without string parsing.
  - Named stages (`FROM ... AS name`) as a first-class concept, which also
    makes `docker build --no-cache-filter <stage>` usable to rebuild one part
    of an image.
  - Knowing the current user and working directory at any point of a builder,
    which the scoped user blocks below can rely on.
  - Package deduplication across calls. Packages are already deduplicated
    within one `add_packages()` call, but the same package requested by two
    composed builders is installed twice. With typed commands, a package
    already installed earlier in the same stage can be dropped from later
    install commands.
  - A natural target for the Dockerfile parser idea above (Dockerfile to AST
    to Pythainer script).

## Planned builders

- CUDA builder
- ROS 2 builder
- Python virtual environment builder. A partial builder that creates a venv
  in the image and installs into it from any combination of a requirements
  file, local package folders (copied through `builder.copy()` and installed
  in editable mode) and a list of package names. It should make sure
  `python3-venv` is installed, set `VIRTUAL_ENV` and prepend the venv's `bin`
  to `PATH` so that the venv interpreter is the default one, and come with a
  test and an example. Idea from #30, to be rewritten on the current
  build-context API rather than rebased.

## Builder API

- Scoped user blocks. Add `as_root()` and `as_user(name="")` on
  `PartialDockerBuilder` as context managers: they emit `USER <name>` on
  entry and switch back to the previous user on exit, where "previous" is
  the last user set on that builder (default `${USER_NAME}`). This replaces
  the manual `builder.root()` ... `builder.user()` pairs without breaking
  them: the existing `user()` and `root()` keep working unchanged. Comes
  with tests and a short example. Idea from #39; a registry of known users
  with validation (the `UserManager` of that PR) is a possible later step,
  as a separate change.

- Quiet builds. `build()` always streams the full `docker build` output. Add
  a way to silence it (showing it only on failure) and a verbose switch to
  get the current behaviour, so that tools built on Pythainer can keep their
  own output readable.

## Planned runners

- Cache volume preset. A partial runner that mounts a persistent cache
  directory or named volume into the container, so that tools that download
  on first use (e.g. Typst packages and fonts) do not download again at every
  run.
- Hardware device preset. A partial runner for flashing and debugging boards
  from inside a container (USB debug probes, serial ports), with the host
  side documented: which udev rules are needed and why they cannot be set
  from the container.

## Python version alignment

- Raise the minimum supported Python version to the one shipped by the
  latest Ubuntu LTS (26.04; exact version to be confirmed), and clean the
  code accordingly (typing syntax, f-strings, standard-library features that
  the older versions lacked).
- Keep every place that states a Python version in sync, in the same change:
  `requires-python` and the trove classifiers in `pyproject.toml`, the
  `target-version` of black and ruff, `python_version` of mypy, the test
  matrix in `.github/workflows/tests.yml` and the interpreter used in
  `.github/workflows/codefmt.yml`. A classifier is only listed if the test
  matrix covers that version.

## Longer term

Directions rather than planned work. Most of them build on the Dockerfile AST
above, with the same goal: environments that can be inspected, checked,
transformed and reproduced. One design boundary applies throughout: an AST of
Dockerfile instructions does not explain arbitrary shell commands. Commands
that are not understood stay opaque, and transformations only apply where the
effect of a command is known.

A sensible first milestone: existing builders populate the structured model,
the model can be inspected, and a small set of checks reports diagnostics at
builder level, demonstrated on one existing composed environment. Import,
manifests and diffs come next; optimization and bundles after that. Recipes,
CI examples and documentation can progress in parallel at any time.

- Inspection. Traversal and serialization of the AST, and for each
  instruction the builder it comes from, so that diagnostics and diffs can
  name the responsible builder.
- Static checks on composition. Detect unpinned dependencies, conflicting
  settings and unresolved references. Let builders declare what they require
  and provide, and runners declare the host capabilities they need (GPU,
  display, devices), so that incompatible compositions are reported before
  the build.
- Image optimization. Merge compatible package installations, improve cache
  reuse, and separate build-time dependencies from what stays in the final
  image (beyond the existing shallow clones, minimal builders and squash).
  Instruction order is preserved unless independence is established, and
  changes are judged on four separate measures: cold build time, incremental
  build time, image size and validation results.
- Semantic diffs between two environments: packages, toolchain versions,
  source revisions, build options, base image and runtime requirements, with
  the builder that introduced each change.
- Locking and provenance. Record base image digests, source commits,
  checksums of inputs, build arguments and context files in a
  machine-readable manifest attached to the built image, and flag the inputs
  that remain mutable. Deterministic Dockerfile rendering does not by itself
  guarantee identical rebuilt images.
- Artifact-evaluation and teaching bundles. Export the builders, the
  generated Dockerfile, the manifest, the runner settings and the
  reproduction instructions together; connect them with benchkit campaigns
  and with student environments. The bundle is an evidence report (checks
  performed, outcomes, remaining assumptions), not a certificate of
  reproducibility.
- Recipe catalogue. Maintain the bundled builders as a catalogue (CUDA,
  ROS 2, OpenCV, Mojo, LLVM/MLIR, QEMU, Rust, RISC-V toolchains) with
  uniform parameters for version, architecture, features and cleanup, and
  compatibility notes. Specialized environments that do not justify
  maintenance stay as worked examples. Add feature-showcase examples that
  demonstrate composition and parameterization end to end.
- CI and image distribution. The same script builds locally and in CI,
  publishes the image and reuses that exact image in later stages; document
  private dependencies (SSH agent forwarding, BuildKit secrets) and cache
  management, with a complete GitLab CI example that builds an image in one
  stage and uses it in the next.
- Stable extension interfaces for builders and runners, as the step towards
  a first non-0.0.x release.
- Exploratory: other container engines behind the same environment
  description (including rootless setups, #15), and assembling an environment
  from declared requirements and compatible recipes.

## Chore

- Move license to VUB.
- Automate the release. `RELEASING.md` is a manual procedure (changelog
  commit, tag, build, `twine upload`). Replace the publishing part with a
  tag-triggered GitHub workflow using PyPI Trusted Publishing, so that a
  release is: changelog commit, tag, push.
- Documentation site (#51), then the corresponding README badge.
- Remaining README badges, each once the thing behind it exists: JOSS paper,
  Zenodo DOI, test coverage (codecov), type checking (mypy, once the strict
  options in `pyproject.toml` are enabled).
