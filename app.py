import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# Constants
EXCEL_FILE = "personal_finance_data.xlsx"
SHEET_BANK = "BankAccounts"
SHEET_MUTUAL = "MutualFunds"
SHEET_STOCKS = "StockHoldings"
SHEET_UDHARI = "Udhari"
SHEET_PF = "ProvisionFund"  # New sheet name for Provision Fund

# Initialize session state for dataframes
if "bank_df" not in st.session_state:
    st.session_state.bank_df = pd.DataFrame(columns=["Account Name", "Balance"])
if "mutual_df" not in st.session_state:
    st.session_state.mutual_df = pd.DataFrame(columns=["Fund Name", "Total Value"])
if "stocks_df" not in st.session_state:
    st.session_state.stocks_df = pd.DataFrame(columns=["Stock", "Total Value"])
if "udhari_df" not in st.session_state:
    st.session_state.udhari_df = pd.DataFrame(columns=["Person", "Amount Owed"])
if "pf_df" not in st.session_state:
    st.session_state.pf_df = pd.DataFrame(columns=["PF Account Name", "Balance"])

def load_data():
    try:
        xls = pd.ExcelFile(EXCEL_FILE)
        st.session_state.bank_df = pd.read_excel(xls, SHEET_BANK)
        st.session_state.mutual_df = pd.read_excel(xls, SHEET_MUTUAL)
        st.session_state.stocks_df = pd.read_excel(xls, SHEET_STOCKS)
        st.session_state.udhari_df = pd.read_excel(xls, SHEET_UDHARI)
        st.session_state.pf_df = pd.read_excel(xls, SHEET_PF)
    except FileNotFoundError:
        # No file yet, keep empty dataframes
        pass
    except Exception as e:
        st.error(f"Error loading data: {e}")

def save_data():
    try:
        with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl", mode="w") as writer:
            st.session_state.bank_df.to_excel(writer, sheet_name=SHEET_BANK, index=False)
            st.session_state.mutual_df.to_excel(writer, sheet_name=SHEET_MUTUAL, index=False)
            st.session_state.stocks_df.to_excel(writer, sheet_name=SHEET_STOCKS, index=False)
            st.session_state.udhari_df.to_excel(writer, sheet_name=SHEET_UDHARI, index=False)
            st.session_state.pf_df.to_excel(writer, sheet_name=SHEET_PF, index=False)
    except Exception as e:
        st.error(f"Error saving data: {e}")

def validate_positive_number(value, field_name):
    if value < 0:
        st.error(f"{field_name} must be non-negative.")
        return False
    return True

def financial_overview():
    st.header("💰 Financial Overview")

    # Calculate totals
    total_bank = st.session_state.bank_df["Balance"].sum() if not st.session_state.bank_df.empty else 0
    total_mutual = st.session_state.mutual_df["Total Value"].sum() if not st.session_state.mutual_df.empty else 0
    total_stocks = st.session_state.stocks_df["Total Value"].sum() if not st.session_state.stocks_df.empty else 0
    total_udhari = st.session_state.udhari_df["Amount Owed"].sum() if not st.session_state.udhari_df.empty else 0
    total_pf = st.session_state.pf_df["Balance"].sum() if not st.session_state.pf_df.empty else 0

    udahri_cash=total_bank+total_udhari
    udhari_cash_stock=udahri_cash+total_mutual+total_stocks
    total_wealth = total_bank + total_mutual + total_stocks + total_udhari + total_pf

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Bank Accounts", f"₹{total_bank:,.2f}")
    col2.metric("Mutual Funds", f"₹{total_mutual:,.2f}")
    col3.metric("Stock Holdings", f"₹{total_stocks:,.2f}")
    col4.metric("Total Udhari", f"₹{total_udhari:,.2f}")
    col5.metric("Provision Fund", f"₹{total_pf:,.2f}")

    st.markdown("---")
    st.subheader("Wealth Summary")
    st.markdown(f"**Cash + Udhari :**  ₹{udahri_cash:,.2f}")
    st.markdown(f"**Cash + Udhari+ Stock:**  ₹{udhari_cash_stock:,.2f}")
    st.markdown(f"**Total Current Wealth:**  ₹{total_wealth:,.2f}")

    # Pie chart of asset distribution (excluding Udhari)
    asset_data = {
        "Bank Accounts": total_bank,
        "Mutual Funds": total_mutual,
        "Stock Holdings": total_stocks,
        "Provision Fund": total_pf,
        "Udhari":total_udhari 
    }
    asset_df = pd.DataFrame({
        "Asset Type": list(asset_data.keys()),
        "Value": list(asset_data.values())
    })
    fig = px.pie(asset_df, values="Value", names="Asset Type", title="Asset Distribution")
    st.plotly_chart(fig, use_container_width=True)

def manage_bank_accounts():
    st.subheader("Bank Accounts")
    df = st.session_state.bank_df

    # Display current accounts
    if df.empty:
        st.info("No bank accounts added yet.")
    else:
        st.dataframe(df.style.format({"Balance": "₹{:,.2f}"}))

    with st.expander("Add New Bank Account"):
        with st.form("add_bank_form", clear_on_submit=True):
            account_name = st.text_input("Account Name", max_chars=50)
            balance = st.number_input("Balance", min_value=0.0, format="%.2f")
            submitted = st.form_submit_button("Add Account")
            if submitted:
                if not account_name.strip():
                    st.error("Account Name cannot be empty.")
                elif not validate_positive_number(balance, "Balance"):
                    pass
                else:
                    new_row = {"Account Name": account_name.strip(), "Balance": balance}
                    st.session_state.bank_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data()
                    st.success(f"Bank account '{account_name}' added.")
                    st.rerun()

    if not df.empty:
        st.markdown("### Edit / Delete Bank Accounts")
        selected_index = st.selectbox("Select account to edit/delete", df.index, format_func=lambda i: df.at[i, "Account Name"])
        if selected_index is not None:
            selected_account = df.loc[selected_index]
            with st.form("edit_bank_form"):
                new_name = st.text_input("Account Name", value=selected_account["Account Name"], max_chars=50)
                new_balance = st.number_input("Balance", min_value=0.0, value=float(selected_account["Balance"]), format="%.2f")
                col1, col2 = st.columns(2)
                with col1:
                    save_btn = st.form_submit_button("Save Changes")
                with col2:
                    delete_btn = st.form_submit_button("Delete Account")
                if save_btn:
                    if not new_name.strip():
                        st.error("Account Name cannot be empty.")
                    elif not validate_positive_number(new_balance, "Balance"):
                        pass
                    else:
                        st.session_state.bank_df.at[selected_index, "Account Name"] = new_name.strip()
                        st.session_state.bank_df.at[selected_index, "Balance"] = new_balance
                        save_data()
                        st.success("Bank account updated.")
                        st.rerun()
                if delete_btn:
                    st.session_state.bank_df = df.drop(selected_index).reset_index(drop=True)
                    save_data()
                    st.success("Bank account deleted.")
                    st.rerun()

def manage_mutual_funds():
    st.subheader("Mutual Funds")
    df = st.session_state.mutual_df

    # Calculate Total Value column if missing or outdated
    if not df.empty:
        st.session_state.mutual_df = df

    if df.empty:
        st.info("No mutual funds added yet.")
    else:
        st.dataframe(df.style.format({ "Total Value": "₹{:,.2f}"}))

    with st.expander("Add New Mutual Fund"):
        with st.form("add_mutual_form", clear_on_submit=True):
            fund_name = st.text_input("Fund Name", max_chars=50)
            total_value=st.number_input('Total Value')
            submitted = st.form_submit_button("Add Mutual Fund")
            if submitted:
                if not fund_name.strip():
                    st.error("Fund Name cannot be empty.")
                elif not validate_positive_number(total_value, "Total Value"):
                    pass
                else:
                    new_row = {"Fund Name": fund_name.strip(),"Total Value": total_value}
                    st.session_state.mutual_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data()
                    st.success(f"Mutual fund '{fund_name}' added.")
                st.rerun()

    if not df.empty:
        st.markdown("### Edit / Delete Mutual Funds")
        selected_index = st.selectbox("Select mutual fund to edit/delete", df.index, format_func=lambda i: df.at[i, "Fund Name"])
        if selected_index is not None:
            selected_fund = df.loc[selected_index]
            with st.form("edit_mutual_form"):
                new_name = st.text_input("Fund Name", value=selected_fund["Fund Name"], max_chars=50)
                total_value = st.number_input("Total Value", min_value=0.0, value=float(selected_fund["Total Value"]), format="%.4f")
                col1, col2 = st.columns(2)
                with col1:
                    save_btn = st.form_submit_button("Save Changes")
                with col2:
                    delete_btn = st.form_submit_button("Delete Fund")
                if save_btn:
                    if not new_name.strip():
                        st.error("Fund Name cannot be empty.")
                    elif not validate_positive_number(total_value, "Units") :
                        pass
                    else:
                        st.session_state.mutual_df.at[selected_index, "Fund Name"] = new_name.strip()
                        st.session_state.mutual_df.at[selected_index, "Total Value"] =total_value
                        save_data()
                        st.success("Mutual fund updated.")
                        st.rerun()
                if delete_btn:
                    st.session_state.mutual_df = df.drop(selected_index).reset_index(drop=True)
                    save_data()
                    st.success("Mutual fund deleted.")
                    st.rerun()
        
def manage_stock_holdings():
    st.subheader("Stock Market Holdings")
    df = st.session_state.stocks_df

    # Calculate Total Value column if missing or outdated
    if not df.empty:
        st.session_state.stocks_df = df

    if df.empty:
        st.info("No stock holdings added yet.")
    else:
        st.dataframe(df.style.format({ "Total Value": "₹{:,.2f}"}))

    with st.expander("Add New Stock Holding"):
        with st.form("add_stock_form", clear_on_submit=True):
           
            Stock = st.text_input("Stock")
            Total_value = st.number_input("Total Value", min_value=0.0, format="%.4f")
            submitted = st.form_submit_button("Add Stock")
            if submitted:
                if not Stock.strip():
                    st.error("Stock Stock cannot be empty.")
                else:
                    new_row = { "Stock": Stock,"Total Value": Total_value}
                    st.session_state.stocks_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data()
                    st.success(f"Stock '{Stock.upper()}' added.")
                    st.rerun()

    if not df.empty:
        st.markdown("### Edit / Delete Stock Holdings")
        selected_index = st.selectbox("Select stock to edit/delete", df.index, format_func=lambda i: df.at[i, "Stock"])
        if selected_index is not None:
            selected_stock = df.loc[selected_index]
            with st.form("edit_stock_form"):
                stock = st.text_input("Stock", value=selected_stock["Stock"], max_chars=10)
                Total_value = st.number_input("Total Value", min_value=0.0, format="%.4f")
                col1, col2 = st.columns(2)
                with col1:
                    save_btn = st.form_submit_button("Save Changes")
                with col2:
                    delete_btn = st.form_submit_button("Delete Stock")
                if save_btn:
                    if not stock.strip():
                        st.error("Stock Symbol cannot be empty.")

                    else:
                        st.session_state.stocks_df.at[selected_index, "Stock"] = stock.strip().upper()
                        st.session_state.stocks_df.at[selected_index, "Total Value"] = Total_value
                        save_data()
                        st.success("Stock holding updated.")
                        st.rerun()
                if delete_btn:
                    st.session_state.stocks_df = df.drop(selected_index).reset_index(drop=True)
                    save_data()
                    st.success("Stock holding deleted.")
                    st.rerun()

def manage_udhari():
    st.subheader("Udhari Tracker")
    df = st.session_state.udhari_df

    if df.empty:
        st.info("No Udhari records yet.")
    else:
        st.dataframe(df.style.format({"Amount Owed": "₹{:,.2f}"}))

    with st.expander("Add New Udhari Record"):
        with st.form("add_udhari_form", clear_on_submit=True):
            person = st.text_input("Person Name", max_chars=50)
            amount = st.number_input("Amount Owed", min_value=0.0, format="%.2f")
            submitted = st.form_submit_button("Add Udhari")
            if submitted:
                if not person.strip():
                    st.error("Person Name cannot be empty.")
                elif not validate_positive_number(amount, "Amount Owed"):
                    pass
                else:
                    new_row = {"Person": person.strip(), "Amount Owed": amount}
                    st.session_state.udhari_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data()
                    st.success(f"Udhari record for '{person}' added.")
                    st.rerun()

    if not df.empty:
        st.markdown("### Edit / Delete Udhari Records")
        selected_index = st.selectbox("Select Udhari record to edit/delete", df.index, format_func=lambda i: df.at[i, "Person"])
        if selected_index is not None:
            selected_udhari = df.loc[selected_index]
            with st.form("edit_udhari_form"):
                new_person = st.text_input("Person Name", value=selected_udhari["Person"], max_chars=50)
                new_amount = st.number_input("Amount Owed", min_value=0.0, value=float(selected_udhari["Amount Owed"]), format="%.2f")
                col1, col2 = st.columns(2)
                with col1:
                    save_btn = st.form_submit_button("Save Changes")
                with col2:
                    delete_btn = st.form_submit_button("Delete Record")
                if save_btn:
                    if not new_person.strip():
                        st.error("Person Name cannot be empty.")
                    elif not validate_positive_number(new_amount, "Amount Owed"):
                        pass
                    else:
                        st.session_state.udhari_df.at[selected_index, "Person"] = new_person.strip()
                        st.session_state.udhari_df.at[selected_index, "Amount Owed"] = new_amount
                        save_data()
                        st.success("Udhari record updated.")
                if delete_btn:
                    st.session_state.udhari_df = df.drop(selected_index).reset_index(drop=True)
                    save_data()
                    st.success("Udhari record deleted.")
                    st.rerun()

def manage_provision_fund():
    st.subheader("Provision Fund")
    df = st.session_state.pf_df

    if df.empty:
        st.info("No Provision Fund records yet.")
    else:
        st.dataframe(df.style.format({"Balance": "₹{:,.2f}"}))

    with st.expander("Add New Provision Fund Record"):
        with st.form("add_pf_form", clear_on_submit=True):
            pf_account_name = st.text_input("PF Account Name", max_chars=50)
            pf_balance = st.number_input("Balance", min_value=0.0, format="%.2f")
            submitted = st.form_submit_button("Add Provision Fund")
            if submitted:
                if not pf_account_name.strip():
                    st.error("PF Account Name cannot be empty.")
                elif not validate_positive_number(pf_balance, "Balance"):
                    pass
                else:
                    new_row = {"PF Account Name": pf_account_name.strip(), "Balance": pf_balance}
                    st.session_state.pf_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data()
                    st.success(f"Provision Fund '{pf_account_name}' added.")
                    st.rerun()

    if not df.empty:
        st.markdown("### Edit / Delete Provision Fund Records")
        selected_index = st.selectbox("Select Provision Fund to edit/delete", df.index, format_func=lambda i: df.at[i, "PF Account Name"])
        if selected_index is not None:
            selected_pf = df.loc[selected_index]
            with st.form("edit_pf_form"):
                new_pf_name = st.text_input("PF Account Name", value=selected_pf["PF Account Name"], max_chars=50)
                new_pf_balance = st.number_input("Balance", min_value=0.0, value=float(selected_pf["Balance"]), format="%.2f")
                col1, col2 = st.columns(2)
                with col1:
                    save_btn = st.form_submit_button("Save Changes")
                with col2:
                    delete_btn = st.form_submit_button("Delete Provision Fund")
                if save_btn:
                    if not new_pf_name.strip():
                        st.error("PF Account Name cannot be empty.")
                    elif not validate_positive_number(new_pf_balance, "Balance"):
                        pass
                    else:
                        st.session_state.pf_df.at[selected_index, "PF Account Name"] = new_pf_name.strip()
                        st.session_state.pf_df.at[selected_index, "Balance"] = new_pf_balance
                        save_data()
                        st.success("Provision Fund record updated.")
                if delete_btn:
                    st.session_state.pf_df = df.drop(selected_index).reset_index(drop=True)
                    save_data()
                    st.success("Provision Fund record deleted.")
                    st.rerun()

def main():
    st.set_page_config(page_title="Personal Finance Dashboard", layout="wide", initial_sidebar_state="expanded")
    st.title("📊 Personal Finance Dashboard")

    # --- Download Excel Button ---
    try:
        with open(EXCEL_FILE, "rb") as f:
            st.download_button(
                label="Download All Data (Excel)",
                data=f,
                file_name=EXCEL_FILE,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except FileNotFoundError:
        st.info("No data file found to download.")

    # --- Upload Excel Button ---
    uploaded_excel = st.file_uploader("Upload Excel to replace ALL data", type=["xlsx"])
    if uploaded_excel is not None:
        try:
            xls = pd.ExcelFile(uploaded_excel)
            st.session_state.bank_df = pd.read_excel(xls, SHEET_BANK)
            st.session_state.mutual_df = pd.read_excel(xls, SHEET_MUTUAL)
            st.session_state.stocks_df = pd.read_excel(xls, SHEET_STOCKS)
            st.session_state.udhari_df = pd.read_excel(xls, SHEET_UDHARI)
            st.session_state.pf_df = pd.read_excel(xls, SHEET_PF)
            # Save uploaded file as the main data file
            with open(EXCEL_FILE, "wb") as f:
                f.write(uploaded_excel.getbuffer())
            st.success("All data replaced successfully.")
            st.rerun()
        except Exception as e:
            st.error(f"Error reading uploaded Excel file: {e}")

    load_data()

    tabs = st.tabs(["Overview", "Bank Accounts", "Mutual Funds", "Stock Holdings", "Udhari Tracker", "Provision Fund"])

    with tabs[0]:
        financial_overview()
    with tabs[1]:
        manage_bank_accounts()
    with tabs[2]:
        manage_mutual_funds()
    with tabs[3]:
        manage_stock_holdings()
    with tabs[4]:
        manage_udhari()
    with tabs[5]:
        manage_provision_fund()

    st.markdown("---")
    st.caption("Developed with ❤️ using Streamlit")
    if st.button('Refresh'):
        st.rerun()

if __name__ == "__main__":
    main()
