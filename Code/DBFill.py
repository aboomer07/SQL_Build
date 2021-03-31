import pandas as pd
import numpy as np
import statsmodels.formula.api as sm
from tabulate import tabulate

################################################################################
# Function to create insert statement for each table from google sheets
################################################################################


def sql_insert(tab, cols, values):

    string = "INSERT INTO \n" + tab + " " + str(tuple(cols)) + "\n"
    string += "VALUES "
    string += ",\n\t".join([str(tuple(row)) for row in values])

    return(string)

################################################################################
# Loop through sheets, filling the database
################################################################################


def fill_db(wsheet, cnxn, tables):

    # elig = """
    # CREATE TRIGGER aid_check
    # BEFORE INSERT ON ACTIONFUND
    # WHEN NEW.FID NOT IN (
    # SELECT DISTINCT ELIGIBILITY.FID
    # FROM ACTION, ELIGIBILITY
    # WHERE ACTION.AID = NEW.AID
    # AND ACTION.TID = ELIGIBILITY.TID)
    # BEGIN
    # SELECT RAISE(FAIL, 'Funding Program not in List of Eligible Programs for this Action Type');
    # END;
    # """

    # cnxn.execute(elig)

    # year = """
    # CREATE TRIGGER year_check
    # BEFORE INSERT ON ACTIONFUND
    # WHEN NEW.AWARDYEAR > (
    # SELECT DISTINCT ACTION.YEAR
    # FROM ACTION
    # WHERE ACTION.AID = NEW.AID)
    # BEGIN
    # SELECT RAISE(FAIL, 'Funding Award Year Cannot After Action Year');
    # END;
    # """

    # cnxn.execute(year)


    # amount = """
    # CREATE TRIGGER amount_check
    # BEFORE INSERT ON ACTIONFUND
    # WHEN NEW.AMOUNT > (
    # SELECT DISTINCT FUNDING.MAXAMOUNT
    # FROM FUNDING, ACTIONFUND
    # WHERE FUNDING.FID = ACTIONFUND.FID)
    # BEGIN
    # SELECT RAISE(FAIL, 'Funded Amount Cannot Be Greater Then Max Amount');
    # END;
    # """

    # cnxn.execute(amount)

    # cumulative = """
    # CREATE TRIGGER cumulative_check 
    # BEFORE INSERT ON ACTIONFUND 
    # WHEN NEW.FID IN (
    # SELECT DISTINCT FID 
    # FROM(
    #     SELECT 1 as Holder, ACTIONFUND.FID 
    #     FROM ACTIONFUND, FUNDING 
    #     WHERE ACTIONFUND.FID = FUNDING.FID 
    #     AND FUNDING.CUMULATIVE = 'FALSE'
    # ) GROUP BY Holder 
    # HAVING COUNT(FID) > 1) 
    # BEGIN SELECT RAISE(FAIL, 'Funding Program is Not Cumulative, Cannot Support Multiple Actions'); 
    # END
    # """

    # cnxn.execute(cumulative)

    # cert = """
    # CREATE TRIGGER cert_check
    # BEFORE INSERT ON LABELLING
    # WHEN NEW.CID NOT IN (
    # SELECT DISTINCT CERTIFYING.CID
    # FROM ACTION, ACTIONTYPE, CERTIFYING
    # WHERE NEW.AID = ACTION.AID 
    # AND ACTION.TID = CERTIFYING.TID)
    # BEGIN
    # SELECT RAISE(FAIL, 'Company Cannot Label This Type Of Action');
    # END;
    # """

    # cnxn.execute(cert)

    insert_str = ""

    for tab in tables:
        col = wsheet.worksheet(tab).get_all_values()[0]
        values = wsheet.worksheet(tab).get_all_values()[1:]
        curr_str = sql_insert(tab, col, values)
        cnxn.execute(curr_str)

        insert_str += "-" * 50 + "\n" + "Filled Table " + tab + "\n"
        insert_str += "-" * 50 + "\n" + curr_str + "\n" + "-" * 50 + "\n\n"

    return(insert_str)

def action_pred(cnxn):
    num_actions = """
    SELECT ACTION.YEAR, AVG(COMPANY.SIZE) as Size,
        AVG(ACTION.LIKES) as NumLikes,
        COUNT(ACTION.AID) as NumActions
    FROM COMPANY, ACTION
    WHERE COMPANY.CID = ACTION.CID
    GROUP BY ACTION.YEAR
    """

    reg_df = pd.DataFrame(cnxn.execute(num_actions).fetchall(),
        columns=['Year', 'Size', 'Likes', 'NumActions'])
    reg_df['SizeLag'] = reg_df['Size'].shift()
    reg_df['LikesLag'] = reg_df['Likes'].shift()
    reg_df['ActionsLag'] = reg_df['NumActions'].shift()

    model = sm.ols(formula="NumActions ~ SizeLag + LikesLag + ActionsLag - 1", 
        data=reg_df)
    result = model.fit()
    exog = reg_df[reg_df['Year'] == 2020][['Size', 'Likes', 'NumActions']]
    exog = exog.T

    pred = 0
    for i in range(len(result.params)):
        pred += (result.params[i] * exog.values[i])

    res_data = pd.DataFrame([[2021, np.round(pred)[0]]],
        columns=['Year', 'NumActions'])

    res_data = pd.concat([reg_df[['Year', 'NumActions']],
        res_data], axis=0, ignore_index=True)

    return(res_data)
