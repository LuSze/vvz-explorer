# VVZ Explorer Data (IPFS)

Data files are available via IPFS for offline use or self-hosting.

## Setup

Follow [Run IPFS inside Docker](https://docs.ipfs.tech/install/run-ipfs-inside-docker/) to spin up a container, or use the one-liner:

```bash
docker run -d --name ipfs_host \
  -p 4001:4001 -p 4001:4001/udp \
  -p 127.0.0.1:8080:8080 \
  -p 127.0.0.1:5001:5001 \
  ipfs/kubo:v0.42.0
```

## Fetch the data

**Individual files** (saved directly to the current directory):

```bash
docker exec ipfs_host ipfs cat QmZgcnVTjiYj9jMjZi1qtURrYocPP5Bj7f5UCcpvXK2fFd > embeddings_FS2026.db
docker exec ipfs_host ipfs cat QmVHNkRj1g9ruZ4tCzbWGkL8obEEfAKH4PUA221WLeJJbS > embeddings_HS2026.db
docker exec ipfs_host ipfs cat QmUMX2SdfQojKFsX1HdMDg9xFJXB4q9Cw1hRnuyf8ca871 > lectures_FS2026.db
docker exec ipfs_host ipfs cat QmV58nZUDYvMwESt9thUgUR3Q8JsFJ5NYQCZaF6Gnz9HbL > lectures_HS2026.db
```

**Whole folder** (all 4 files at once — uses `ipfs get` inside the container, then `docker cp` to the host):

```bash
docker exec ipfs_host ipfs get QmYdcVjzaTmVD5DYjLgdbB9m2G7VfCVzbq2QrDjfpiiHJ3
docker cp ipfs_host:/QmYdcVjzaTmVD5DYjLgdbB9m2G7VfCVzbq2QrDjfpiiHJ3/. ./vvz_explorer_data
```

## Cleanup

```bash
docker rm -f ipfs_host
```

## Files

| File | Size | CID |
|------|------|-----|
| `embeddings_FS2026.db` | ~90 MB | `QmZgcnVTjiYj9jMjZi1qtURrYocPP5Bj7f5UCcpvXK2fFd` |
| `embeddings_HS2026.db` | ~91 MB | `QmVHNkRj1g9ruZ4tCzbWGkL8obEEfAKH4PUA221WLeJJbS` |
| `lectures_FS2026.db` | ~8.3 MB | `QmUMX2SdfQojKFsX1HdMDg9xFJXB4q9Cw1hRnuyf8ca871` |
| `lectures_HS2026.db` | ~8.0 MB | `QmV58nZUDYvMwESt9thUgUR3Q8JsFJ5NYQCZaF6Gnz9HbL` |
| **Root folder** | — | `QmYdcVjzaTmVD5DYjLgdbB9m2G7VfCVzbq2QrDjfpiiHJ3` |

## Provenance

PeerID: `12D3KooWH5CDMj9XZkSjhtadiCVi7K4hpt5AgyNaEt4S9pruhiXS`

Verify that your node fetched the data from this peer:

```bash
ipfs routing findprovs QmYdcVjzaTmVD5DYjLgdbB9m2G7VfCVzbq2QrDjfpiiHJ3
```

## HTTP gateways

If you can't or don't want to run an IPFS node, use an HTTP gateway:

[https://ipfs.github.io/public-gateway-checker/](https://ipfs.github.io/public-gateway-checker/)

Pick a working gateway and download with `curl` or `wget`:

```bash
curl -o lectures_FS2026.db \
  https://<your-chosen-gateway>/ipfs/QmUMX2SdfQojKFsX1HdMDg9xFJXB4q9Cw1hRnuyf8ca871
```

> **Note:** Gateway access depends on the operator being able to reach a provider. If your chosen gateway fails, try another from the checker, or use the Docker/IPFS method above.
