from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

print(HtmlFormatter(style="material").get_style_defs('.codehilite'))
