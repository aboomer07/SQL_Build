from DB_Connect import *
from itertools import combinations

q_dict = {
    'F1': 'Create a form/view that displays companies of a given sector and their actions',
    'F1.5': 'Showcase functionality of view F1.',
    'R1': 'Information about the evolution through time of companies of a given sector.',
    'R2': "Number of granted (funded) actions and the total amount of grants received by sector. Limit to sectors having received more than X grants and sort according to the amount. Give also a graphic representation of the answer.",
    'R3': "For each type of actions display the companies that can help for its realization.",
    'R4': "Number of companies by location. Give a world map chart (import in excel the data..., look for a tutorial about that).",
    'R5': "Companies in the decreasing order of the total number of likes they got through their actions.",
    'R6': "The company that got the most number of certified actions.",
    'R7': "Companies that propose help and also provide certifications.",
    'R8': "Companies whose green situation has been improved between two given years: the quantity of carbon emissions decreases.",
    'R9': "Evolution of the investment of a given company per year: number of recruitments, the percentage of green investment compared to the amount of turnover. Give also a graphic representation.",
    'F2': "Form that displays for each funding program the type of actions it can fund.",
    'F2.5': 'Showcase functionality of view F2.',
    'R10': "Average, max and min amounts of grants and number of grants attributed by each Funding program.",
    'R11': "Types of actions without funding program.",
    'R12': "Evolution by year of the total amount received by granted actions. Draw also a graphic.",
    'R13': "Percentage of actions that were funded.",
    'Open': "Taking all the necessary assumptions and using the tools of your choice (R, Python...) combined with SQL, try to forecast how the number of actions will evolve in the future"
}

pkg_dict = {
    'F1':"Package 1",
    'F1.5':"Package 1",
    'R1':"Package 1",
    'R2':"Package 1",
    'R3':"Package 1",
    'R4':"Package 1",
    'R5':"Package 2",
    'R6':"Package 2",
    'R7':"Package 2",
    'R8':"Package 2",
    'R9':"Package 2",
    'F2':"Package 3",
    'F2.5':"Package 3",
    'R10':"Package 3",
    'R11':"Package 3",
    'R12':"Package 3",
    'R13':"Package 3",
    'Open': "Open Question"
}


def get_sql(cnxn):
    year_res = [i[0] for i in cnxn.execute(
        "SELECT DISTINCT Year FROM IMPROVEMENT").fetchall()]
    yr_combs = [i for i in combinations(year_res, 2) if i[1] == i[0] + 1]

    emiss = ",\n\t".join([
        """sum(Emissions) filter(where Year = %s) - sum(Emissions) filter(where Year = %s) Diff%s%s""" % (str(yr[1]), str(yr[0]), str(yr[1]), str(yr[0])) for yr in yr_combs])

    emiss_lim = " OR ".join(["Diff%s%s < 0" % (
        str(yr[1]), str(yr[0])) for yr in yr_combs])

    sql_dict = {
        'F1': """
SELECT COMPANY.CID, COMPANY.NAME, ACTION.AID
FROM COMPANY, ACTION
WHERE COMPANY.CID = ACTION.CID""",
        'F1.5': """
SELECT * FROM """,
        'R1': """
SELECT IMPROVEMENT.*, COMPANY.NAME
FROM COMPANY, IMPROVEMENT 
WHERE COMPANY.CID = IMPROVEMENT.CID""",
        'R2': """
SELECT COMPANY.SECTOR,
	COUNT(ACTIONFUND.FID) As GrantedActions, 
	SUM(ACTIONFUND.Amount) as TotalAmount 
FROM COMPANY, ACTION, ACTIONFUND 
WHERE COMPANY.CID = ACTION.CID 
AND ACTION.AID = ACTIONFUND.AID 
GROUP BY COMPANY.SECTOR 
HAVING GrantedActions > 0 
ORDER BY TotalAmount DESC""",
        'R3': """
SELECT ACTIONTYPE.TID, ACTIONTYPE.DESCRIPTION,
	COMPANY.CID, COMPANY.NAME 
FROM ACTIONTYPE, CERTIFYING, COMPANY 
WHERE COMPANY.CID = CERTIFYING.CID 
AND ACTIONTYPE.TID = CERTIFYING.TID""",
        'R4': """
SELECT Country, COUNT(CID) as NumCompanies 
FROM COMPANY 
GROUP BY Country
ORDER BY NumCompanies DESC""",
        'R5': """
SELECT COMPANY.CID, COMPANY.Name, 
	SUM(ACTION.Likes) AS NumLikes 
FROM ACTION, COMPANY 
WHERE ACTION.CID = COMPANY.CID 
GROUP BY COMPANY.Name 
ORDER BY NumLikes DESC""",
        'R6': """
SELECT COMPANY.CID, COMPANY.Name, 
COUNT(LABELLING.AID) as NumCerts 
FROM COMPANY, LABELLING, ACTION
WHERE COMPANY.CID = ACTION.CID AND
LABELLING.AID = ACTION.AID 
GROUP BY COMPANY.CID, COMPANY.Name
ORDER BY NumCerts DESC LIMIT 3""",
        'R7': """
SELECT DISTINCT comb.CID, COMPANY.Name
FROM(
	SELECT DISTINCT CID
	FROM SUPPORTING 

	UNION ALL 

	SELECT DISTINCT CID
	FROM CERTIFYING
) comb, COMPANY
WHERE comb.CID = COMPANY.CID""",
        'R8': """
SELECT COMPANY.CID, COMPANY.Name, 
	%s 
FROM COMPANY, IMPROVEMENT 
WHERE COMPANY.CID = IMPROVEMENT.CID 
GROUP BY COMPANY.CID 
HAVING %s""" % (emiss, emiss_lim),
        'F2':"""
CREATE VIEW EligibleTypes AS
SELECT FUNDING.FID, FUNDING.NAME, ACTIONTYPE.TID, ACTIONTYPE.DESCRIPTION
FROM FUNDING, ACTIONTYPE, ELIGIBILITY
WHERE FUNDING.FID = ELIGIBILITY.FID AND ELIGIBILITY.TID = ACTIONTYPE.TID""",
        'F2.5':"""
SELECT * FROM EligibleTypes""",
        'R9': """
SELECT COMPANY.CID, COMPANY.Name, Year,
	GreenRecruit, GreenInvest, Turnover, 
	(GreenInvest/Turnover)*100 AS GreenInvestPercentage
FROM COMPANY, IMPROVEMENT 
WHERE COMPANY.CID = IMPROVEMENT.CID""",
        'R10': """
SELECT FUNDING.FID, 
	AVG(ACTIONFUND.Amount) as AvgAmount, 
	MAX(ACTIONFUND.Amount) as MaxAmount, 
	MIN(ACTIONFUND.Amount) as MinAmount, 
	COUNT(ACTIONFUND.AID) as NumGrants 
FROM FUNDING, ACTIONFUND 
WHERE FUNDING.FID = ACTIONFUND.FID 
GROUP BY FUNDING.FID""",
        'R11': """
SELECT ACTIONTYPE.TID, ACTIONTYPE.DESCRIPTION
FROM ACTIONTYPE 
WHERE ACTIONTYPE.TID NOT IN(
SELECT ACTION.TID FROM
ACTION, ACTIONFUND
WHERE ACTION.AID = ACTIONFUND.AID)""",
        'R12': """
SELECT AwardYear, SUM(Amount) as YearlyAmt 
FROM ACTIONFUND 
GROUP BY AwardYear""",
        'R13': """
SELECT 100 * CAST(Funded AS DECIMAL) / CAST(AllActions AS DECIMAL) as PctFunded 
FROM(
	SELECT 1 As Holder, COUNT(AID) As Funded 
	FROM ACTIONFUND 
	GROUP BY Holder
) AS left 
JOIN (
	SELECT 1 As Holder, COUNT(AID) As AllActions 
	FROM ACTION 
	GROUP BY Holder
) AS right 
ON left.Holder = right.Holder""",
        'Open': """
SELECT ACTION.YEAR, AVG(COMPANY.SIZE) as Size,
    SUM(ACTION.LIKES) as NumLikes,
    COUNT(ACTION.AID) as NumActions
FROM COMPANY, ACTION
WHERE COMPANY.CID = ACTION.CID
GROUP BY ACTION.YEAR

NumActions(t) = A*Size(t-1) + B*NumLikes(t-1) + C*NumActions(t-1)
        """,
    }

    col_dict = {
        'F1': ['CID', 'Name', 'AID'],
        'F1.5': ['CID', 'Name', 'AID'],
        'R1': ['IID', 'Emissions', 'Turnover', 'GreenInvest', 'GreenRecruit', 'CID', 'Year', 'Name'],
        'R2': ['Sector', 'GrantedActions', 'TotalAmount'],
        'R3': ['TID', 'Description', 'CID', 'NAME'],
        'R4': ['Location', 'NumCompanies'],
        'R5': ['CID', 'Name', 'NumLikes'],
        'R6': ['CID', 'Name', 'NumCerts'],
        'R7': ['CID', 'Name'],
        'R8': ['CID', 'Name'] + ['Diff_%s_%s' % (str(yr[1]), str(yr[0])) for yr in yr_combs],
        'R9': ['CID', 'Name', 'Year', 'GreenRecruit', 'GreenInvest', 'Turnover', 'GreenInvestPercentage'],
        'F2': ['FID', 'Name', 'TID', 'Description'],
        'F2.5': ['FID', 'Name', 'TID', 'Description'],
        'R10': ['FID', 'AvgAmount', 'MaxAmount', 'MinAmount', 'NumGrants'],
        'R11': ['TID', 'Description'],
        'R12': ['AwardYear', 'YearlyAmt'],
        'R13': ['PctFunded'],
        'Open': ['Year', 'Prediction']
    }

    return(sql_dict, col_dict)
