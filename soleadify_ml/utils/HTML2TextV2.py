import re

from html2text import HTML2Text, element_style, google_has_height, hn, escape_md, google_list_style, \
    list_numbering_start
from html2text import config
from html2text.compat import urlparse


class HTML2TextV2(HTML2Text):

    def __init__(self, out=None, baseurl='', bodywidth=config.BODY_WIDTH):
        self.get_email_phone = False
        super().__init__(out=out, baseurl=baseurl, bodywidth=bodywidth)

    def handle_tag(self, tag, attrs, start):
        self.current_tag = tag
        # attrs is None for endtags
        if attrs is None:
            attrs = {}
        else:
            attrs = dict(attrs)

        if self.tag_callback is not None:
            if self.tag_callback(self, tag, attrs, start) is True:
                return

        # first thing inside the anchor tag is another tag
        # that produces some output
        if (start and self.maybe_automatic_link is not None and
                tag not in ['p', 'div', 'style', 'dl', 'dt'] and
                (tag != "img" or self.ignore_images)):
            self.o("[")
            self.maybe_automatic_link = None
            self.empty_link = False

        if self.google_doc:
            # the attrs parameter is empty for a closing tag. in addition, we
            # need the attributes of the parent nodes in order to get a
            # complete style description for the current element. we assume
            # that google docs export well formed html.
            parent_style = {}
            if start:
                if self.tag_stack:
                    parent_style = self.tag_stack[-1][2]
                tag_style = element_style(attrs, self.style_def, parent_style)
                self.tag_stack.append((tag, attrs, tag_style))
            else:
                dummy, attrs, tag_style = self.tag_stack.pop() \
                    if self.tag_stack else (None, {}, {})
                if self.tag_stack:
                    parent_style = self.tag_stack[-1][2]

        if hn(tag):
            self.p()
            if start:
                self.inheader = True
                self.o(hn(tag) * "#" + ' ')
            else:
                self.inheader = False
                return  # prevent redundant emphasis marks on headers

        if tag in ['p', 'div']:
            if self.google_doc:
                if start and google_has_height(tag_style):
                    self.p()
                else:
                    self.soft_br()
            elif self.astack and tag == 'div':
                pass
            else:
                self.p()

        if tag == "br" and start:
            if self.blockquote > 0:
                self.o("  \n> ")
            else:
                self.o("  \n")

        if tag == "hr" and start:
            self.p()
            self.o("* * *")
            self.p()

        if tag in ["head", "style", 'script']:
            if start:
                self.quiet += 1
            else:
                self.quiet -= 1

        if tag == "style":
            if start:
                self.style += 1
            else:
                self.style -= 1

        if tag in ["body", "title"]:
            self.quiet = 0  # sites like 9rules.com never close <head>

        if tag == "blockquote":
            if start:
                self.p()
                self.o('> ', 0, 1)
                self.start = 1
                self.blockquote += 1
            else:
                self.blockquote -= 1
                self.p()

        def no_preceding_space(self):
            return (self.preceding_data
                    and re.match(r'[^\s]', self.preceding_data[-1]))

        if tag in ['em', 'i', 'u', 'span'] and not self.ignore_emphasis:
            if start and no_preceding_space(self):
                emphasis = ' ' + self.emphasis_mark
            else:
                emphasis = self.emphasis_mark

            self.o(emphasis)
            if start:
                self.stressed = True

        if tag in ['strong', 'b'] and not self.ignore_emphasis:
            if start and no_preceding_space(self):
                strong = ' ' + self.strong_mark
            else:
                strong = self.strong_mark

            self.o(strong)
            if start:
                self.stressed = True

        if tag in ['del', 'strike', 's']:
            if start and no_preceding_space(self):
                strike = ' ~~'
            else:
                strike = '~~'

            self.o(strike)
            if start:
                self.stressed = True

        if self.google_doc:
            if not self.inheader:
                # handle some font attributes, but leave headers clean
                self.handle_emphasis(start, tag_style, parent_style)

        if tag in ["kbd", "code", "tt"] and not self.pre:
            self.o('`')  # TODO: `` `this` ``
            self.code = not self.code

        if tag == "abbr":
            if start:
                self.abbr_title = None
                self.abbr_data = ''
                if ('title' in attrs):
                    self.abbr_title = attrs['title']
            else:
                if self.abbr_title is not None:
                    self.abbr_list[self.abbr_data] = self.abbr_title
                    self.abbr_title = None
                self.abbr_data = ''

        if tag == "q":
            if not self.quote:
                self.o(self.open_quote)
            else:
                self.o(self.close_quote)
            self.quote = not self.quote

        def link_url(self, link, title="", separator1='(', separator2=')'):
            url = urlparse.urljoin(self.baseurl, link)
            title = ' "{0}"'.format(title) if title.strip() else ''
            self.o((']' + separator1 + '{url}{title}' + separator2 + '').format(url=escape_md(url),
                                                                                title=title))

        if tag == "a" and not self.ignore_links:
            if start:
                if 'href' in attrs and \
                        attrs['href'] is not None and not \
                        (self.skip_internal_links and
                         attrs['href'].startswith('#')):
                    self.astack.append(attrs)
                    self.maybe_automatic_link = attrs['href']
                    self.empty_link = True
                    if self.protect_links:
                        attrs['href'] = '<' + attrs['href'] + '>'
                else:
                    self.astack.append(None)
            else:
                if self.astack:
                    a = self.astack.pop()
                    if self.maybe_automatic_link and not self.empty_link:
                        self.maybe_automatic_link = None
                    elif a:
                        is_phone_or_email = False
                        if self.empty_link:
                            self.o("[")
                            self.empty_link = False
                            self.maybe_automatic_link = None
                        if self.inline_links:
                            href = a['href']
                            if self.get_email_phone:
                                if 'tel' in href or 'mailto' in href:
                                    is_phone_or_email = True
                            try:
                                title = a['title'] if a['title'] else ''
                                title = escape_md(title)
                            except KeyError:
                                if self.get_email_phone:
                                    if is_phone_or_email:
                                        link_url(self, a['href'], '', ' ', ' ')
                                else:
                                    link_url(self, a['href'], '', ' ', ' ')
                            else:
                                if self.get_email_phone:
                                    if is_phone_or_email:
                                        link_url(self, a['href'], title, ' ', ' ')
                                else:
                                    link_url(self, a['href'], title, ' ', ' ')
                        else:
                            i = self.previousIndex(a)
                            if i is not None:
                                a = self.a[i]
                            else:
                                self.acount += 1
                                a['count'] = self.acount
                                a['outcount'] = self.outcount
                                self.a.append(a)
                            self.o("][" + str(a['count']) + "]")

        if tag == "img" and start and not self.ignore_images:
            if 'src' in attrs:
                if not self.images_to_alt:
                    attrs['href'] = attrs['src']
                alt = attrs.get('alt') or self.default_image_alt

                # If we have images_with_size, write raw html including width,
                # height, and alt attributes
                if self.images_with_size and \
                        ("width" in attrs or "height" in attrs):
                    self.o("<img src='" + attrs["src"] + "' ")
                    if "width" in attrs:
                        self.o("width='" + attrs["width"] + "' ")
                    if "height" in attrs:
                        self.o("height='" + attrs["height"] + "' ")
                    if alt:
                        self.o("alt='" + alt + "' ")
                    self.o("/>")
                    return

                # If we have a link to create, output the start
                if self.maybe_automatic_link is not None:
                    href = self.maybe_automatic_link
                    if self.images_to_alt and escape_md(alt) == href and \
                            self.absolute_url_matcher.match(href):
                        self.o("<" + escape_md(alt) + ">")
                        self.empty_link = False
                        return
                    else:
                        self.o("[")
                        self.maybe_automatic_link = None
                        self.empty_link = False

                # If we have images_to_alt, we discard the image itself,
                # considering only the alt text.
                if self.images_to_alt:
                    self.o(escape_md(alt))
                else:
                    self.o("![" + escape_md(alt) + "]")
                    if self.inline_links:
                        href = attrs.get('href') or ''
                        self.o(
                            "(" +
                            escape_md(
                                urlparse.urljoin(
                                    self.baseurl,
                                    href
                                )
                            ) +
                            ")"
                        )
                    else:
                        i = self.previousIndex(attrs)
                        if i is not None:
                            attrs = self.a[i]
                        else:
                            self.acount += 1
                            attrs['count'] = self.acount
                            attrs['outcount'] = self.outcount
                            self.a.append(attrs)
                        self.o("[" + str(attrs['count']) + "]")

        if tag == 'dl' and start:
            self.p()
        if tag == 'dt' and not start:
            self.pbr()
        if tag == 'dd' and start:
            self.o('    ')
        if tag == 'dd' and not start:
            self.pbr()

        if tag in ["ol", "ul"]:
            # Google Docs create sub lists as top level lists
            if (not self.list) and (not self.lastWasList):
                self.p()
            if start:
                if self.google_doc:
                    list_style = google_list_style(tag_style)
                else:
                    list_style = tag
                numbering_start = list_numbering_start(attrs)
                self.list.append({
                    'name': list_style,
                    'num': numbering_start
                })
            else:
                if self.list:
                    self.list.pop()
                    if (not self.google_doc) and (not self.list):
                        self.o('\n')
            self.lastWasList = True
        else:
            self.lastWasList = False

        if tag == 'li':
            self.pbr()
            if start:
                if self.list:
                    li = self.list[-1]
                else:
                    li = {'name': 'ul', 'num': 0}
                if self.google_doc:
                    nest_count = self.google_nest_count(tag_style)
                else:
                    nest_count = len(self.list)
                # TODO: line up <ol><li>s > 9 correctly.
                self.o("  " * nest_count)
                if li['name'] == "ul":
                    self.o(self.ul_item_mark + " ")
                elif li['name'] == "ol":
                    li['num'] += 1
                    self.o(str(li['num']) + ". ")
                self.start = 1

        if tag in ["table", "tr", "td", "th"]:
            if self.ignore_tables:
                if tag == 'tr':
                    if start:
                        pass
                    else:
                        self.soft_br()
                else:
                    pass

            elif self.bypass_tables:
                if start:
                    self.soft_br()
                if tag in ["td", "th"]:
                    if start:
                        self.o('<{0}>\n\n'.format(tag))
                    else:
                        self.o('\n</{0}>'.format(tag))
                else:
                    if start:
                        self.o('<{0}>'.format(tag))
                    else:
                        self.o('</{0}>'.format(tag))

            else:
                if tag == "table":
                    if start:
                        self.table_start = True
                        if self.pad_tables:
                            self.o("<" + config.TABLE_MARKER_FOR_PAD + ">")
                            self.o("  \n")
                    else:
                        if self.pad_tables:
                            self.o("</" + config.TABLE_MARKER_FOR_PAD + ">")
                            self.o("  \n")
                if tag in ["td", "th"] and start:
                    if self.split_next_td:
                        self.o(" ")
                    self.split_next_td = True

                if tag == "tr" and start:
                    self.td_count = 0
                if tag == "tr" and not start:
                    self.split_next_td = False
                    self.soft_br()
                if tag == "tr" and not start and self.table_start:
                    # Underline table header
                    self.o("|".join(["---"] * self.td_count))
                    self.soft_br()
                    self.table_start = False
                if tag in ["td", "th"] and start:
                    self.td_count += 1

        if tag == "pre":
            if start:
                self.startpre = 1
                self.pre = 1
            else:
                self.pre = 0
                if self.mark_code:
                    self.out("\n[/code]")
            self.p()
