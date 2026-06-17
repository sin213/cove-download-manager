import sys

if "--native-messaging" in sys.argv:
    from .native_messaging import main
    main()
else:
    from .app import run
    sys.exit(run())
