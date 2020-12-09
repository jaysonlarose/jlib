#!/usr/bin/env python3
import jlib, enum, time

class TextSpinner:
	def __init__(self, position_chars = ['│', '╱', '─', '╲']):
		self.position_chars = position_chars
		self.position = 0
	def tick(self):
		self.position += 1
	@property
	def char(self):
		return self.position_chars[self.position % len(self.position_chars)]
	@property
	def value(self):
		return self.char

class SpinnerCycle(enum.Enum):
	SIMULTANEOUS=0
	CHARSFIRST=1
	COLORSFIRST=2
	COLORSDURATION=3

spinner_chars_1 = ['│', '╱', '─', '╲']
spinner_chars_x = ['▘', '▝', '▗', '▖', '▀', '▐', '▄', '▌', '▜', '▟', '▙', '▛', '█', '▜', '▟', '▙', '▛', '▀', '▐', '▄', '▌', '▘', '▝', '▗', '▖', ' ']

spinner_chars_2 = [
'▘', '▝', '▗', '▖',
'▌', '▀', '▐', '▄',
'▙', '▛', '▜', '▟',
'█',
'▙', '▛', '▜', '▟',
'▌', '▀', '▐', '▄',
'▘', '▝', '▗', '▖',
' ',
]
spinner_chars_3 = ['▘', '▝', '▗', '▖']
spinner_chars_4 = ['┌', '┐', '┘', '└']

class FabulousSpinner:
	def __init__(self, position_chars = spinner_chars_2, spectrum_length=255*3, spectrum_duration=60.0, cycle_mode=SpinnerCycle.COLORSDURATION, force=False, fg256=False):
		self.position_chars = position_chars
		self.spectrum_length = spectrum_length
		self.spectrum_duration = spectrum_duration
		self.cycle_mode = cycle_mode
		self.position = 0
		fab = jlib.get_fabulous(force=force)
		self.fgfunc = fab['fgtrue']
		if fg256:
			self.fgfunc = fab['fg256']
		self.bold = fab['bold']
	def tick(self, offset=1):
		self.position += offset 
	@property
	def char(self):
		import colorsys

		if self.cycle_mode == SpinnerCycle.CHARSFIRST:
			charpos = self.position % len(self.position_chars)
			colorpos = ((self.position // len(self.position_chars)) % self.spectrum_length) / self.spectrum_length
		elif self.cycle_mode == SpinnerCycle.COLORSFIRST:
			charpos = (self.position // self.spectrum_length) % len(self.position_chars)
			colorpos = (self.position % self.spectrum_length) / self.spectrum_length
		elif self.cycle_mode == SpinnerCycle.SIMULTANEOUS:
			charpos = self.position % len(self.position_chars)
			colorpos = (self.position % self.spectrum_length) / self.spectrum_length
		elif self.cycle_mode == SpinnerCycle.COLORSDURATION:
			charpos = self.position % len(self.position_chars)
			colorpos = (time.monotonic() % self.spectrum_duration) / self.spectrum_duration
		fgc = '#' + ''.join([ "{:02x}".format(int(x * 255)) for x in colorsys.hsv_to_rgb(colorpos, 1.0, 1.0) ])
		return self.bold(self.fgfunc(fgc, self.position_chars[charpos]))
	@property
	def value(self):
		return self.char

try:
	if __name__ == '__main__':
		import JaysTerm, argparse, locale
		locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())
		parser = argparse.ArgumentParser()
		parser.add_argument("--chars", action="store", dest="chars", default=None)
		parser.add_argument("--256", action="store_true", dest="fg256", default=False)
		parser.add_argument("-l", action="store", dest="spectrum_length", type=int, default=None)
		parser.add_argument("-1", "--oneshot", action="store", dest="tick", type=int, default=None)
		args = parser.parse_args()

		spinner_kwargs = {}
		if args.chars is not None:
			spinner_kwargs['position_chars'] = globals()[args.chars]
		if args.fg256:
			spinner_kwargs['fg256'] = True
		if args.spectrum_length is not None:
			spinner_kwargs['spectrum_length'] = args.spectrum_length
		spinner_kwargs['force'] = True

		spinner = FabulousSpinner(**spinner_kwargs)
		if args.tick is not None:
			spinner.tick(args.tick)
			print(spinner.char)
		else:
			JaysTerm.Term.init()
			l = JaysTerm.UpdatingLine()
			while True:
				l.update("{} {:n} {}".format(spinner.char, spinner.position, (time.monotonic() % spinner.spectrum_duration) / spinner.spectrum_duration))
				time.sleep(0.1)
				spinner.tick()
except KeyboardInterrupt:
	pass
