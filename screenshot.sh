#!/bin/sh

# Requires the infobeamer screenshot utility

ssh raspi 'screenshot > /tmp/screen.jpg'
scp raspi:/tmp/screen.jpg .

imv screen.jpg
rm screen.jpg
