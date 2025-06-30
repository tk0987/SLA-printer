# SLA-3D-printer
raspberry pi zero W based SLA printer. After creating proper library changing usb to gpio-like tool will be usable with old laptops or pc.

html gui. this SLA printer wont use other gui than this web one. It will be fully-wifi based, compatible with every web browser, including mobile.

as an UV screen i'll use 7 inch LCD screen without back (a'la mono!), 1024x600 px, which gives ~160 microns/pixel. Its HDMI screen, it works just fine with raspberry pi zero. And human eye (even shortsighted like mine) wont see each individual pixel.

theres a small possibility that I'll need to remove those color filters from pixels, then replace polarizer. If so, I will leave a note here about that. Most probably my uv leds will do their work without that, but exposure time may be slightly longer than in original mono screens. we'll see.

3, 2, 1... start

basic motor and gui connection added. next:
1. refine motor control code - partially done
2. drive lcd for printing - done
3. check it all and refine if needed - done.


remember about permissions in the upload directory.

