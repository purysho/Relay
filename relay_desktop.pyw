from __future__ import annotations

import argparse

from relay.app import RelayApp


def parse_args(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--url')
    parser.add_argument('--method', default='GET')
    return parser.parse_known_args(argv)[0]


def main(argv=None):
    args = parse_args(argv)
    app = RelayApp()
    if args.url:
        app.url.set(args.url)
    method = str(args.method or 'GET').upper()
    if method in {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'}:
        app.method.set(method)
    app.mainloop()


if __name__ == '__main__':
    main()
