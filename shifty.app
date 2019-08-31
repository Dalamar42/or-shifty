#!/usr/bin/env python3
import logging

import shifty.app
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
shifty.app.main()
