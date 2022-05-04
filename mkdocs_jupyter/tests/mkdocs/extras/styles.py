from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

print(HtmlFormatter(style="material").get_style_defs('.codehilite'))
