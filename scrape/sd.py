from spatula.pages import JsonListPage
from spatula.core import Workflow, URL
from common import Person


class DirectoryListing(JsonListPage):
    source = URL("https://sdlegislature.gov/api/SessionMembers/Session/44")

    def process_item(self, item):

        first = item["FirstName"]
        last = item["LastName"]
        initial = item["Initial"]

        if initial:
            name = f"{first} {initial}. {last}"
        else:
            name = f"{first} {last}"

        p = Person(
            name=name,
            family_name=last,
            given_name=first,
            state="sd",
            district=item["District"].lstrip("0"),
            chamber="upper" if item["MemberType"] == "S" else "lower",
            party=item["Politics"],
            email=item["EmailState"],
            image="https://lawmakerdocuments.blob.core.usgovcloudapi.net/photos/"
            + item["Picture"].lower(),
        )

        address = item["HomeAddress1"]
        if item["HomeAddress2"]:
            address += "; " + item["HomeAddress2"]
        address += f"{item['HomeCity']}, {item['HomeState']} {item['HomeZip']}"

        p.district_office.address = address
        p.district_office.voice = item["HomePhone"]
        p.capitol_office.voice = item["CapitolPhone"]
        p.extras["occupation"] = item["Occupation"]

        url = f"https://sdlegislature.gov/Legislators/Profile/{item['SessionMemberId']}/Detail"
        p.add_link(url)
        p.add_source(url)
        return p


legislators = Workflow(DirectoryListing())
