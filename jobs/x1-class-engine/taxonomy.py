"""Order types for X1, the lifecycle class engine.

Each type has a lifecycle class (how its orders usually end, which decides the
cheaper research path), the type-rule id that covers it, and keyword patterns.
Patterns run on *compact* text: lower case with every character that is not a
letter or digit removed, because the WPA list's OCR both joins words
("Desertersfrom") and splits them ("com pensation"). A pattern match is a lead
for the type; it is never a finding about the order's legal status.

Classes:
  spent    ended by its own performance (a one-person waiver, an allotment, a closing day)
  land     a reservation, withdrawal or boundary of public land (often still in force)
  swept    a candidate for one later mass-ending event (see EVENTS.json)
  standing a known type that still needs order-by-order research
  unknown  no pattern matched
"""
import re

# (type_id, class, rule_id or "", strength, patterns). Order is precedence:
# the first type whose pattern matches a source wins for that source.
# strength: "strong" patterns are specific phrases; "weak" ones are generic words.
TYPES = [
    # --- swept by a mass-ending event --------------------------------------
    ("nra_code_approval", "swept", "TR-NRA-CODE", "strong",
     [r"codeoffaircompetition", r"codesoffaircompetition", r"nationalindustrialrecovery", r"nationalrecoveryadministration",
      r"\bnra\b", r"supplementarycode", r"codeauthority", r"divisionoftheconstructionindustry", r"constructionindustry", r"presidentsreemploymentagreement", r"retailcode"]),
    # --- spent on issue --------------------------------------------------------
    ("retirement_exemption", "spent", "TR-RETIREMENT-EXEMPTION", "strong",
     [r"compulsoryretire", r"exempt\w{0,20}retire", r"retirementprovisions", r"retirementact", r"retirementage",
      r"continuedin(the)?service(beyond|after|until|for)", r"retain\w{0,12}inthe?service(beyond|after|until)",
      r"beyondtheageof", r"agelimit\w{0,10}retire"]),
    ("cs_waiver_individual", "spent", "TR-CS-WAIVER", "strong",
     [r"withoutexamination", r"withoutregardtothecivilservice", r"madeeligibleto", r"eligibleto(reenter|bereinstated|beappointed|retain|transfer)", r"withoutregardto\w{0,10}age", r"eligibilit\w{0,20}(for)?reinstatement", r"withoutregardtoprovisionofeo", r"permittedtotake\w{0,40}examination", r"withoutregardtocivilservice",
      r"withoutcompliancewiththecivilservice", r"notwithstanding\w{0,40}civilservice",
      r"madeeligiblefor", r"(is|are)?eligiblefor(re)?(appointment|instatement|transfer|promotion|retention)",
      r"authorizedto(be)?(re)?(appoint|instate|transfer|employ)\w{0,80}withoutregard",
      r"(re)?instate(d|ment)\w{0,60}(withoutregard|notwithstanding|withoutexamination)",
      r"classifiedstatus", r"competitivestatus", r"civilservicestatus",
      r"waiv\w{0,30}civilservice", r"civilservice\w{0,40}waiv", r"exceptedfrom(the)?civilservice\w{0,20}(examination|rules)"]),
    ("tax_return_inspection", "spent", "TR-TAX-RETURN-INSPECTION", "strong",
     [r"inspectionof\w{0,40}returns", r"open(ed)?toinspection",
      r"taxreturns\w{0,40}(inspect|examin)", r"inspect\w{0,40}taxreturns"]),
    ("alien_property_sale", "spent", "TR-ALIEN-PROPERTY-SALE", "strong",
     [r"alienpropertycustodian\w{0,80}(sell|sale|resell|bids|dispose|auction)", r"(sell|sale)\w{0,60}alienproperty"]),
    ("labor_hours_suspension", "spent", "TR-EIGHT-HOUR-SUSPENSION", "strong",
     [r"eighthour(day|law|workday)?\w{0,60}(suspend|waiv)", r"(suspend|waiv)\w{0,60}eighthour"]),
    ("fund_allotment", "spent", "TR-FUND-ALLOTMENT", "strong",
     [r"allot(ment|ted|ting)?(of|offunds|funds|from)", r"allocat(ion|ing|ed)?(of)?funds", r"fundsallocated",
      r"(allocated|allotted|transferred)\w{0,30}from\w{0,40}emergencyrelief", r"transfer(of|ring)?funds", r"fundsavailable", r"fundstransferred",
      r"publicworksfund", r"advance\w{0,6}funds", r"allocatedto", r"allottedto", r"madeavailablefrom", r"(sum|amount)of\d+\w{0,40}(allocated|allotted|madeavailable|transferred)", r"appropriation\w{0,40}(allot|allocat|transfer|apportion)", r"(allot|allocat)\w{0,40}appropriation"]),
    ("closing_mourning", "spent", "TR-CLOSING-MOURNING", "strong",
     [r"(departments?|offices|executivedepartments|governmentoffices|federaloffices|navyyards?|stations)\w{0,60}closed",
      r"closed\w{0,30}(onaccount|inrespect|asamark|tomorrow|onthe(day|afternoon))", r"halfholiday", r"mourning",
      r"halfstaff", r"halfmast", r"holiday", r"employees\w{0,40}excused", r"laborday", r"closingof\w{0,40}(departments|offices)", r"(excused|dismissed)\w{0,40}(employees|duty)",
      r"funeral", r"inrespecttothememory", r"asamarkofrespect"]),
    # --- land ----------------------------------------------------------------
    ("public_water_reserve", "land", "TR-WATER-RESERVE", "strong",
     [r"publicwaterreserve", r"waterreserve", r"springsandwaterholes", r"wateringplace", r"waterholes?"]),
    ("power_site_reserve", "land", "TR-POWER-SITE", "strong",
     [r"powersite", r"reservoirsite", r"powerpurposes", r"waterpower", r"powerprojects?"]),
    ("stock_driveway", "land", "TR-STOCK-DRIVEWAY", "strong",
     [r"stockdriveway", r"driveway"]),
    ("bird_refuge", "land", "TR-BIRD-REFUGE", "strong",
     [r"birdreserv", r"birdrefuge", r"wildliferefuge", r"gamerefuge", r"gamepreserve", r"gamereserv",
      r"migratorybird", r"breedinggroundfor\w{0,30}birds", r"refugeforbirds", r"wildlife", r"reservationfornativebirds",
      r"nativebirds", r"birdpreserv", r"waterfowl", r"refuge"]),
    ("lighthouse_reservation", "land", "TR-LIGHTHOUSE", "strong",
     [r"lighthouse(purposes|reserv|site|station|service\w{0,20}land)", r"forlighthouse", r"lightstation", r"lightandfogsignal"]),
    ("national_forest_boundary", "land", "TR-NATIONAL-FOREST", "strong",
     [r"nationalforest"]),
    ("mineral_withdrawal", "land", "TR-MINERAL-WITHDRAWAL", "strong",
     [r"oilshale", r"petroleumreserve", r"navalpetroleum", r"navaloilshale", r"coallands?", r"phosphate", r"potash",
      r"helium", r"oilandgas", r"petroleum\w{0,20}withdraw", r"withdraw\w{0,80}(oil|coal|phosphate|potash|mineral)",
      r"classification\w{0,30}(oil|coal|mineral)", r"(oil|coal|mineral)\w{0,30}classification"]),
    ("military_naval_reservation", "land", "TR-MILITARY-RESERVATION", "strong",
     [r"militaryreservation", r"navalreservation", r"militarypurposes", r"navalpurposes", r"navalradio",
      r"navalstation", r"forthe(use|purposes)ofthe(war|navy)department", r"forusebythe(war|navy)department",
      r"targetrange", r"rifle(and\w{0,20})?range", r"aviationfield", r"fortifications", r"militarypost",
      r"coastdefense", r"lighthousereservation\w{0,30}military"]),
    ("indian_reservation_trust", "land", "TR-INDIAN-RESERVATION", "strong",
     [r"indianreservation", r"trustperiod", r"indianallotment", r"allotments?(to|of)\w{0,40}indians",
      r"fortheuseof\w{0,30}indians", r"indians?\w{0,60}(reservation|allotment|reserve)", r"(reservation|allotment|reserve)\w{0,40}indians?\b",
      r"pueblo"]),
    ("land_withdrawal_general", "land", "TR-LAND-WITHDRAWAL", "strong",
     [r"withdraw(n|al|ing)?\w{0,60}(land|entry|settlement|sale|disposal|location)", r"reservedpending", r"pendingresurvey", r"(land|lands|tract|island|acres)\w{0,80}withdraw",
      r"reserved(for|from)", r"setapart", r"setaside\w{0,40}(land|for)", r"(land|lands)\w{0,60}(restored|reserved|reserve)",
      r"restored(to|for)(the)?(publicdomain|entry|settlement)", r"publicdomain", r"publiclands?", r"townsite",
      r"schoolsite", r"cemetery", r"naturalmonument", r"nationalmonument", r"(revok|modif)\w{0,40}withdrawal",
      r"withdrawalfor\w{0,30}(classification|use)", r"temporarywithdrawal", r"administrativesite",
      r"\bacres\b", r"described(lands|tracts?|area)", r"certainlands", r"islands?\w{0,40}(reserved|withdrawn|setapart)"]),
    # --- standing: known types still needing order-by-order research ---------
    ("property_transfer", "spent", "TR-PROPERTY-TRANSFER", "strong",
     [r"(vessel|uss|ship|steamer|planter|boat|yacht|archives|records|filesandpapers|equipment|materials|supplies)\w{0,80}transferred",
      r"transferofthe(vessel|uss|ship|steamer)", r"(vessel|ship|steamer)\w{0,60}(retransfer|return)"]),
    ("own_terms_expiry", "spent", "TR-OWN-TERMS-EXPIRY", "strong",
     [r"timelimit\w{0,80}extended", r"(continued|extended|deferred|postponed)(further)?until", r"furtherdeferred",
      r"(furthercontinued|furtherextended)until"]),
    ("canal_zone", "swept", "TR-CANAL-ZONE", "strong",
     [r"canalzone", r"panamacanal", r"isthmiancanal", r"isthmusofpanama"]),
    ("patent_signing_designation", "standing", "", "strong",
     [r"signthepresidentsname", r"sign\w{0,30}landpatents"]),
    ("defensive_sea_area", "standing", "", "strong",
     [r"defensivesearea", r"navalairspacereservation", r"airspacereservation"]),
    ("state_office_permission", "standing", "", "strong",
     [r"(hold|holding)\w{0,30}(local|state|territorial|county|municipal)\w{0,30}office", r"participatein\w{0,30}elections"]),
    ("cs_rules_amendment", "standing", "", "strong",
     [r"civilservicerules?", r"schedulea", r"scheduleb", r"schedulec", r"rule[ivxl]+\w{0,30}(amended|revised)",
      r"civilserviceregulations", r"classifiedservice", r"\d{4}csr\d", r"civilservice", r"civilservicecommission", r"(examination|eligible)s?register"]),
    ("philippines", "swept", "TR-PHILIPPINES", "strong",
     [r"philippineislands", r"philippinegovernment", r"governmentofthephilippine", r"governorgeneral\w{0,20}philippine",
      r"commonwealthofthephilippines", r"philippinescouts", r"philippinecommission", r"philippineconstabulary",
      r"philippinelegislature", r"philippinecivilservice", r"\bp\s?i\b"]),
    # --- swept (date-gated): First World War emergency measures ---------------
    ("wwi_emergency", "swept", "TR-WWI-EMERGENCY", "strong",
     [r"warindustriesboard", r"wartradeboard", r"warfinancecorporation", r"warlabor", r"warrisk", r"tradingwiththeenemy",
      r"alienenem", r"enemyalien", r"enemy", r"espionage", r"censorship", r"censor", r"foodadministrat", r"fueladministrat",
      r"selectiveservice", r"emergencyfleet", r"shippingboard", r"exportlicen", r"exportcontrol", r"exportsof",
      r"housingcorporation", r"duringthe(existing)?war", r"durationofthewar", r"existingemergency",
      r"councilofnationaldefense", r"overmanact", r"libertyloan", r"warsavings", r"directorgeneralofrailroads",
      r"federalcontrol", r"waremergency", r"publicinformation", r"warcollege\b", r"stateofwar", r"thewarwith(germany|austria)",
      r"forthedurationofthewar", r"warpurposes", r"wartime", r"warmaterials", r"warcontracts", r"warneeds"]),
    ("consular_foreign_service", "standing", "", "strong",
     [r"consular", r"diplomatic", r"foreignservice", r"legation", r"consul\w{0,10}general", r"ambassador"]),
    ("tariff_customs", "standing", "", "strong",
     [r"customs", r"tariff(?!ofconsularfees)", r"portsofentry", r"portofentry", r"collectiondistrict", r"customsdistrict",
      r"tonnage"]),
    ("territories", "standing", "", "weak",
     [r"alaska", r"hawaii", r"puertorico", r"portorico", r"virginislands", r"guam", r"samoa", r"tutuila", r"cuba"]),
    ("pay_allowances", "standing", "", "weak",
     [r"compensation", r"salar(y|ies)", r"allowance", r"perdiem", r"travel(ing|ling)?expenses", r"\bpay\b", r"wages", r"rentalallowance"]),
    ("personnel_designation", "standing", "", "weak",
     [r"appointed", r"designated", r"detailed", r"assigned", r"actingas", r"tosucceed"]),
    ("organization_agency", "standing", "", "weak",
     [r"landdistrict", r"landoffice", r"surveyorgeneral", r"established", r"created", r"abolished", r"transferred", r"consolidated", r"reorganiz", r"board", r"commission",
      r"council", r"committee", r"bureau"]),
    ("regulations_issuance", "standing", "", "weak",
     [r"regulations?", r"rules(and|governing|for)", r"prescribed", r"amended"]),
]

# A type is skipped for a source when one of its negative patterns matches.
NEGATIVE = {
    "closing_mourning": [r"saturday\w{0,80}(summer|julyaugust|junejuly|duringthemonths|eachweek|fourhour)",
                         r"(summer|duringthemonths)\w{0,80}saturday"],
    "property_transfer": [r"functions", r"duties", r"division", r"bureau\w{0,30}transferred", r"abolish"],
    "fund_allotment": [r"regulations\w{0,40}(governing|for|prescribed)"],
}
_NEG = {k: [re.compile(p) for p in v] for k, v in NEGATIVE.items()}

TYPE_CLASS = {t[0]: t[1] for t in TYPES}
TYPE_RULE = {t[0]: t[2] for t in TYPES}
TYPE_STRENGTH = {t[0]: t[3] for t in TYPES}
_COMPILED = [(t[0], [re.compile(p) for p in t[4]]) for t in TYPES]

# The First World War emergency type applies only to orders dated in the war
# emergency (declaration of war 1917-04-06 to the joint resolution of 1921-03-03).
WWI_FROM, WWI_TO = 1917, 1921

APP_GENERIC_TITLE = re.compile(r"^executive order(\s+no\.?\s*[\w-]+)?$|^executive order\s*[-—]\s*$", re.I)


def compact(text):
    """Lower case, letters and digits only, words joined."""
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def spaced(text):
    return " " + re.sub(r"[^a-z0-9]+", " ", (text or "").lower()) + " "


def matches(text, year=None):
    """All (type_id, pattern) hits in one source, in precedence order.

    Short word patterns (with \\b) are tested on spaced text, others on compact text."""
    c, s = compact(text), spaced(text)
    out = []
    for type_id, pats in _COMPILED:
        if type_id == "wwi_emergency" and not (year and WWI_FROM <= year <= WWI_TO):
            continue
        if any(n.search(c) for n in _NEG.get(type_id, [])):
            continue
        for p in pats:
            hay = s if "\\b" in p.pattern else c
            m = p.search(hay)
            if m:
                out.append((type_id, p.pattern, m.group(0)))
                break
    return out
