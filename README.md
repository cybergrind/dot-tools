# dot-tools

A grab bag of small scripts I use to keep my dotfiles and projects in shape.
Nothing fancy — just the stuff I got tired of rewriting.

Install it however you prefer (`pip install dot-tools`, `uv tool install dot-tools`, etc.)
and you'll get the commands below on your `PATH`.

## What's in the box

### `traefik_run`
Spins up a local Traefik via docker-compose. Pass extra args after `--`.

```bash
traefik_run              # up -d
traefik_run -- ps -a
traefik_run -- down
```

### `handle_envrc`
Keeps `.envrc` files synced across machines through a shared folder
(set `ENVRC_HOME`, defaults to `~/.keys/envrc`).
`handle_envrc migrate` moves storage from the old location (`--old`, defaults to
`~/Yandex.Disk/home/envrc`) to `ENVRC_HOME`, re-points all symlinks under `--root`
(default: `~/devel`) and re-approves them with `direnv allow`.
If the local `.envrc` isn't a symlink yet, it moves it into the shared dir
and replaces it with a link. If a shared one exists but the link is missing, it restores it.

```bash
handle_envrc
```

### `add_dot_files`
Drops common project boilerplate into the current directory:
`.editorconfig`, `pyproject.toml`, `.pre-commit-config.yaml`, `.yamllint`, `.projectile`.

```bash
add_dot_files
```

### `cpuniq`
Copy (or move) files into a directory without clobbering. If the name is taken
and the content differs, it appends a short uuid suffix.

```bash
cpuniq photo.jpg ~/pictures/
cpuniq -m mv *.log ~/archive/
```

### `release.py`
Bumps the version, tags, builds and uploads. Mostly for this repo's own release flow.

```bash
release.py master
release.py -v 1.2.3 master
```

## License

MIT.
