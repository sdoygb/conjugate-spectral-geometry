"""Command-line interface.

Usage:
  qec-cert certify -r 2 -m 6 [--samples 3000] [--no-w2-full]
  qec-cert brute -r 1 -m 5 [--max-w 4] [--verbose]
  qec-cert family
"""
from __future__ import annotations

import argparse
import json

from .certificate import certify
from .rm_codes import FAMILY_EXAMPLES, css_params
from .brute import brute_verify


def _cmd_certify(args: argparse.Namespace) -> None:
    cert = certify(
        r=args.r,
        m=args.m,
        n_samples=args.samples,
        seed=args.seed,
        do_w2_full=not args.no_w2_full,
    )
    print(cert.summary())
    if args.json:
        print(json.dumps(cert.to_dict(), indent=2))


def _cmd_brute(args: argparse.Namespace) -> None:
    layers = brute_verify(
        r=args.r,
        m=args.m,
        max_w=args.max_w,
        verbose=args.verbose,
    )
    s = layers.pop("_summary")
    print(f"[[{s['n']},{s['k']},{s['d']}]] brute weight<= "
          f"{max(k for k in layers)} : {s['total_flips']:,} flips, "
          f"undetected={s['total_undetected']}, {s['elapsed']:.2f}s")
    if args.verbose:
        for w, v in sorted(layers.items()):
            print(f"  w={w}: total={v['total']:,}, undetected={v['undetected']}, "
                  f"{v['elapsed']:.2f}s")


def _cmd_family(_args: argparse.Namespace) -> None:
    print("Verified CSS(RM(r,m)) code family members:")
    for r, m in FAMILY_EXAMPLES:
        n, k, d = css_params(r, m)
        print(f"  RM({r},{m}) -> [[{n},{k},{d}]]")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(
        prog="qec-cert",
        description="Distance certificate verification for CSS(RM) "
                    "affine-complete codes (distance-certifying, no enumeration)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("certify", help="verify the distance and print the certificate")
    pc.add_argument("-r", type=int, required=True, help="RM order")
    pc.add_argument("-m", type=int, required=True,
                    help="number of variables (self-orthogonality requires 2r < m-1)")
    pc.add_argument("--samples", type=int, default=3000,
                    help="number of sampling-corroboration samples")
    pc.add_argument("--seed", type=int, default=260807)
    pc.add_argument("--no-w2-full", action="store_true",
                    help="skip the full weight-2 cross-check")
    pc.add_argument("--json", action="store_true",
                    help="output the certificate as JSON")
    pc.set_defaults(func=_cmd_certify)

    pb = sub.add_parser("brute", help="brute-force enumeration baseline (reference path)")
    pb.add_argument("-r", type=int, required=True)
    pb.add_argument("-m", type=int, required=True)
    pb.add_argument("--max-w", type=int, default=None,
                    help="enumerate up to weight max-w (default d-1)")
    pb.add_argument("--verbose", action="store_true")
    pb.set_defaults(func=_cmd_brute)

    pf = sub.add_parser("family", help="list the verified family members")
    pf.set_defaults(func=_cmd_family)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
