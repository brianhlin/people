import re
from spatula.pages import HtmlListPage
from spatula.selectors import XPath
from common import Person


def clean_name(name):
    name = re.sub(r"\s+", " ", name)
    name = name.strip()
    return name.title()


class Legislators(HtmlListPage):
    session_num = "113"
    source = "https://leg.mt.gov/legislator-information/?session_select=" + session_num
    selector = XPath("//table[1]/tbody/tr")

    def process_item(self, item):
        tds = item.getchildren()
        email, name, party, seat, phone = tds

        chamber, district = seat.text_content().strip().split()
        url = str(name.xpath("a/@href")[0])

        person = Person(
            name=clean_name(name.text_content()),
            state="mt",
            party=party.text_content().strip(),
            chamber=("upper" if chamber == "SD" else "lower"),
            district=district,
        )
        person.add_link(url)
        person.add_source(url)

        phone = phone.text_content().strip()
        if len(phone) == 14:
            person.capitol_office.voice = phone
        elif len(phone) > 30:
            person.capitol_office.voice = phone.split("    ")[0]

        email = email.xpath("./a/@href")
        if email:
            email = email[0].split(":", 1)[1]
        person.capitol_office.email = email

        return person
