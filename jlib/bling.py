# Classes and routines for making stuff look sweet.


def termformat_pygmentize(code, lexername, stylename="fruity"):
	import pygments, pygments.lexers, pygments.formatters, pygments.util, pygments.styles
	lexer = pygments.lexers.get_lexer_by_name(lexername)
	#formatter = pygments.formatters.terminal.TerminalFormatter()
	#stylee = pygments.styles.get_style_by_name(stylename)
	formatter = pygments.formatters.get_formatter_by_name("terminal16m").__class__(style=pygments.styles.get_style_by_name(stylename))
	#formatter.encoding = pygments.util.terminal_encoding(sys.stdout)
	return pygments.highlight(code, lexer, formatter)



# Script for extracting EGA palettes from wikipedia table{{{
##!/usr/bin/env python3
#import bs4, tinycss2
#data = """\
#<table class="wikitable" style="text-align: center">
#  <caption><b>EGA color palette</b></caption>
#  <tbody>
#    <tr style="color:white;">
#      <td style="background:#000; width:3pc;" title="#000"><u>0x00</u></td>
#      <td style="background:#005; width:3pc;" title="#005">0x01</td>
#      <td style="background:#500; width:3pc;" title="#505">0x02</td>
#      <td style="background:#505; width:3pc;" title="#505">0x03</td>
#      <td style="background:#050; width:3pc;" title="#050">0x04</td>
#      <td style="background:#055; width:3pc;" title="#055">0x05</td>
#      <td style="background:#550; width:3pc;" title="#550">0x06</td>
#      <td style="background:#555; width:3pc;" title="#555"><u>0x07</u></td>
#    </tr>
#    <tr style="color:white;">
#      <td style="background:#00a; width:3pc;" title="#00A"><u>0x08</u></td>
#      <td style="background:#00f; width:3pc;" title="#00F">0x09</td>
#      <td style="background:#50a; width:3pc;" title="#50A">0x0A</td>
#      <td style="background:#50f; width:3pc;" title="#50F">0x0B</td>
#      <td style="background:#05a; width:3pc;" title="#05A">0x0C</td>
#      <td style="background:#05f; width:3pc;" title="#05F">0x0D</td>
#      <td style="background:#55a; width:3pc;" title="#55A">0x0E</td>
#      <td style="background:#55f; width:3pc;" title="#55F"><u>0x0F</u></td>
#    </tr>
#    <tr>
#      <td style="color:white; background:#a00; width:3pc;" title="#A00"><u>0x10</u></td>
#      <td style="color:white; background:#a05; width:3pc;" title="#A05">0x11</td>
#      <td style="color:white; background:#f00; width:3pc;" title="#F00">0x12</td>
#      <td style="color:white; background:#f05; width:3pc;" title="#F05">0x13</td>
#      <td style="color:white; background:#a50; width:3pc;" title="#A50"><u>0x14</u></td>
#      <td style="color:white; background:#a55; width:3pc;" title="#A55">0x15</td>
#      <td style="color:white; background:#f50; width:3pc;" title="#F50">0x16</td>
#      <td style="color:black; background:#f55; width:3pc;" title="#F55"><u>0x17</u></td>
#    </tr>
#    <tr>
#      <td style="color:white; background:#a0a; width:3pc;" title="#A0A"><u>0x18</u></td>
#      <td style="color:white; background:#a0f; width:3pc;" title="#A0F">0x19</td>
#      <td style="color:white; background:#f0a; width:3pc;" title="#F0A">0x1A</td>
#      <td style="color:white; background:#f0f; width:3pc;" title="#F0F">0x1B</td>
#      <td style="color:white; background:#a5a; width:3pc;" title="#A5A">0x1C</td>
#      <td style="color:white; background:#a5f; width:3pc;" title="#A5F">0x1D</td>
#      <td style="color:black; background:#f5a; width:3pc;" title="#F5A">0x1E</td>
#      <td style="color:black; background:#f5f; width:3pc;" title="#F5F"><u>0x1F</u></td>
#    </tr>
#    <tr>
#      <td style="color:white; background:#0a0; width:3pc;" title="#0A0"><u>0x20</u></td>
#      <td style="color:white; background:#0a5; width:3pc;" title="#0A5">0x21</td>
#      <td style="color:white; background:#5a0; width:3pc;" title="#5A0">0x22</td>
#      <td style="color:black; background:#5a5; width:3pc;" title="#5A5">0x23</td>
#      <td style="color:white; background:#0f0; width:3pc;" title="#0F0">0x24</td>
#      <td style="color:black; background:#0f5; width:3pc;" title="#0F5">0x25</td>
#      <td style="color:black; background:#5f0; width:3pc;" title="#5F0">0x26</td>
#      <td style="color:black; background:#5f5; width:3pc;" title="#5F5"><u>0x27</u></td>
#    </tr>
#    <tr>
#      <td style="color:white; background:#0aa; width:3pc;" title="#0AA"><u>0x28</u></td>
#      <td style="color:white; background:#0af; width:3pc;" title="#0AF">0x29</td>
#      <td style="color:black; background:#5aa; width:3pc;" title="#5AA">0x2A</td>
#      <td style="color:black; background:#5af; width:3pc;" title="#5AF">0x2B</td>
#      <td style="color:black; background:#0fa; width:3pc;" title="#0FA">0x2C</td>
#      <td style="color:black; background:#0ff; width:3pc;" title="#0FF">0x2D</td>
#      <td style="color:black; background:#5fa; width:3pc;" title="#5FA">0x2E</td>
#      <td style="color:black; background:#5ff; width:3pc;" title="#5FF"><u>0x2F</u></td>
#    </tr>
#    <tr style="color:black;">
#      <td style="background:#aa0; width:3pc;" title="#AA0">0x30</td>
#      <td style="background:#aa5; width:3pc;" title="#AA5">0x31</td>
#      <td style="background:#fa0; width:3pc;" title="#FA0">0x32</td>
#      <td style="background:#fa5; width:3pc;" title="#FA5">0x33</td>
#      <td style="background:#af0; width:3pc;" title="#AF0">0x34</td>
#      <td style="background:#af5; width:3pc;" title="#AF5">0x35</td>
#      <td style="background:#ff0; width:3pc;" title="#FF0">0x36</td>
#      <td style="background:#ff5; width:3pc;" title="#FF5"><u>0x37</u></td>
#    </tr>
#    <tr style="color:black;">
#      <td style="background:#aaa; width:3pc;" title="#AAA"><u>0x38</u></td>
#      <td style="background:#aaf; width:3pc;" title="#AAF">0x39</td>
#      <td style="background:#faa; width:3pc;" title="#FAA">0x3A</td>
#      <td style="background:#faf; width:3pc;" title="#FAF">0x3B</td>
#      <td style="background:#afa; width:3pc;" title="#AFA">0x3C</td>
#      <td style="background:#aff; width:3pc;" title="#AFF">0x3D</td>
#      <td style="background:#ffa; width:3pc;" title="#FFA">0x3E</td>
#      <td style="background:#fff; width:3pc;" title="#FFF"><u>0x3F</u></td>
#    </tr>
#  </tbody>
#</table>
#"""
#
#if __name__ == '__main__':
#	soup = bs4.BeautifulSoup(data, "lxml")
#	ega_total_palette = [ [ int("{0}{0}".format(c), 16) for c in cx ] for cx in [ [ s.value[0].value for s in tinycss2.parse_declaration_list(x['style']) if s.type == 'declaration' and s.name == 'background' ][0] for x in soup.find_all('td') ] ]
#	ega_default_palette = [ [ int("{0}{0}".format(c), 16) for c in cx ] for cx in [ [ s.value[0].value for s in tinycss2.parse_declaration_list(x['style']) if s.type == 'declaration' and s.name == 'background' ][0] for x in soup.find_all('td') if len(x.find_all('u')) > 0 ] ]
#
#	for x in ['ega_default_palette', 'ega_total_palette']:
#		print("{} = {}".format(x, repr(globals()[x])))
# }}}


ega_default_palette = [[0, 0, 0], [85, 85, 85], [0, 0, 170], [85, 85, 255], [170, 0, 0], [170, 85, 0], [255, 85, 85], [170, 0, 170], [255, 85, 255], [0, 170, 0], [85, 255, 85], [0, 170, 170], [85, 255, 255], [255, 255, 85], [170, 170, 170], [255, 255, 255]]
ega_total_palette = [[0, 0, 0], [0, 0, 85], [85, 0, 0], [85, 0, 85], [0, 85, 0], [0, 85, 85], [85, 85, 0], [85, 85, 85], [0, 0, 170], [0, 0, 255], [85, 0, 170], [85, 0, 255], [0, 85, 170], [0, 85, 255], [85, 85, 170], [85, 85, 255], [170, 0, 0], [170, 0, 85], [255, 0, 0], [255, 0, 85], [170, 85, 0], [170, 85, 85], [255, 85, 0], [255, 85, 85], [170, 0, 170], [170, 0, 255], [255, 0, 170], [255, 0, 255], [170, 85, 170], [170, 85, 255], [255, 85, 170], [255, 85, 255], [0, 170, 0], [0, 170, 85], [85, 170, 0], [85, 170, 85], [0, 255, 0], [0, 255, 85], [85, 255, 0], [85, 255, 85], [0, 170, 170], [0, 170, 255], [85, 170, 170], [85, 170, 255], [0, 255, 170], [0, 255, 255], [85, 255, 170], [85, 255, 255], [170, 170, 0], [170, 170, 85], [255, 170, 0], [255, 170, 85], [170, 255, 0], [170, 255, 85], [255, 255, 0], [255, 255, 85], [170, 170, 170], [170, 170, 255], [255, 170, 170], [255, 170, 255], [170, 255, 170], [170, 255, 255], [255, 255, 170], [255, 255, 255]]


def morse_encode(text):
	return text.replace('.', '•').replace('-', '╺')

def morse_decode(morse):
	return text.replace('•', '.').replace('╺', '-')
