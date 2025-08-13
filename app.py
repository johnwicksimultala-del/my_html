
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

# Initialize session state for dataframes
if "bank_df" not in st.session_state:
    st.session_state.bank_df = pd.DataFrame(columns=["Account Name", "Balance"])
if "mutual_df" not in st.session_state:
    st.session_state.mutual_df = pd.DataFrame(columns=["Fund Name", "Units", "NAV", "Total Value"])
if "stocks_df" not in st.session_state:
    st.session_state.stocks_df = pd.DataFrame(columns=["Stock Symbol", "Shares", "Price", "Total Value"])
if "udhari_df" not in st.session_state:
    st.session_state.udhari_df = pd.DataFrame(columns=["Person", "Amount Owed"])

def load_data():
    try:
        xls = pd.ExcelFile(EXCEL_FILE)
        st.session_state.bank_df = pd.read_excel(xls, SHEET_BANK)
        st.session_state.mutual_df = pd.read_excel(xls, SHEET_MUTUAL)
        st.session_state.stocks_df = pd.read_excel(xls, SHEET_STOCKS)
        st.session_state.udhari_df = pd.read_excel(xls, SHEET_UDHARI)
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

    total_wealth = total_bank + total_mutual + total_stocks + total_udhari

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Bank Accounts", f"₹{total_bank:,.2f}")
    col2.metric("Mutual Funds", f"₹{total_mutual:,.2f}")
    col3.metric("Stock Holdings", f"₹{total_stocks:,.2f}")
    col4.metric("Total Udhari", f"₹{total_udhari:,.2f}")

    st.markdown("---")
    st.subheader("Wealth Summary")
    st.markdown(f"**Total Current Wealth:**  ₹{total_wealth:,.2f}")

    # Pie chart of asset distribution (excluding Udhari)
    asset_data = {
        "Bank Accounts": total_bank,
        "Mutual Funds": total_mutual,
        "Stock Holdings": total_stocks,
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
                if delete_btn:
                    st.session_state.bank_df = df.drop(selected_index).reset_index(drop=True)
                    save_data()
                    st.success("Bank account deleted.")

def manage_mutual_funds():
    st.subheader("Mutual Funds")
    df = st.session_state.mutual_df

    # Calculate Total Value column if missing or outdated
    if not df.empty:
        df["Total Value"] = df["Units"] * df["NAV"]
        st.session_state.mutual_df = df

    if df.empty:
        st.info("No mutual funds added yet.")
    else:
        st.dataframe(df.style.format({"Units": "{:.2f}", "NAV": "₹{:,.2f}", "Total Value": "₹{:,.2f}"}))

    with st.expander("Add New Mutual Fund"):
        with st.form("add_mutual_form", clear_on_submit=True):
            fund_name = st.text_input("Fund Name", max_chars=50)
            units = st.number_input("Units", min_value=0.0, format="%.4f")
            nav = st.number_input("NAV (Net Asset Value)", min_value=0.0, format="%.4f")
            submitted = st.form_submit_button("Add Mutual Fund")
            if submitted:
                if not fund_name.strip():
                    st.error("Fund Name cannot be empty.")
                elif not validate_positive_number(units, "Units") or not validate_positive_number(nav, "NAV"):
                    pass
                else:
                    total_value = units * nav
                    new_row = {"Fund Name": fund_name.strip(), "Units": units, "NAV": nav, "Total Value": total_value}
                    st.session_state.mutual_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data()
                    st.success(f"Mutual fund '{fund_name}' added.")

    if not df.empty:
        st.markdown("### Edit / Delete Mutual Funds")
        selected_index = st.selectbox("Select mutual fund to edit/delete", df.index, format_func=lambda i: df.at[i, "Fund Name"])
        if selected_index is not None:
            selected_fund = df.loc[selected_index]
            with st.form("edit_mutual_form"):
                new_name = st.text_input("Fund Name", value=selected_fund["Fund Name"], max_chars=50)
                new_units = st.number_input("Units", min_value=0.0, value=float(selected_fund["Units"]), format="%.4f")
                new_nav = st.number_input("NAV", min_value=0.0, value=float(selected_fund["NAV"]), format="%.4f")
                col1, col2 = st.columns(2)
                with col1:
                    save_btn = st.form_submit_button("Save Changes")
                with col2:
                    delete_btn = st.form_submit_button("Delete Fund")
                if save_btn:
                    if not new_name.strip():
                        st.error("Fund Name cannot be empty.")
                    elif not validate_positive_number(new_units, "Units") or not validate_positive_number(new_nav, "NAV"):
                        pass
                    else:
                        st.session_state.mutual_df.at[selected_index, "Fund Name"] = new_name.strip()
                        st.session_state.mutual_df.at[selected_index, "Units"] = new_units
                        st.session_state.mutual_df.at[selected_index, "NAV"] = new_nav
                        st.session_state.mutual_df.at[selected_index, "Total Value"] = new_units * new_nav
                        save_data()
                        st.success("Mutual fund updated.")
                if delete_btn:
                    st.session_state.mutual_df = df.drop(selected_index).reset_index(drop=True)
                    save_data()
                    st.success("Mutual fund deleted.")

def manage_stock_holdings():
    st.subheader("Stock Market Holdings")
    df = st.session_state.stocks_df

    # Calculate Total Value column if missing or outdated
    if not df.empty:
        df["Total Value"] = df["Shares"] * df["Price"]
        st.session_state.stocks_df = df

    if df.empty:
        st.info("No stock holdings added yet.")
    else:
        st.dataframe(df.style.format({"Shares": "{:.2f}", "Price": "₹{:,.2f}", "Total Value": "₹{:,.2f}"}))

    with st.expander("Add New Stock Holding"):
        with st.form("add_stock_form", clear_on_submit=True):
            symbol = st.text_input("Stock Symbol", max_chars=10)
            shares = st.number_input("Shares", min_value=0.0, format="%.4f")
            price = st.number_input("Price per Share", min_value=0.0, format="%.4f")
            submitted = st.form_submit_button("Add Stock")
            if submitted:
                if not symbol.strip():
                    st.error("Stock Symbol cannot be empty.")
                elif not validate_positive_number(shares, "Shares") or not validate_positive_number(price, "Price"):
                    pass
                else:
                    total_value = shares * price
                    new_row = {"Stock Symbol": symbol.strip().upper(), "Shares": shares, "Price": price, "Total Value": total_value}
                    st.session_state.stocks_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data()
                    st.success(f"Stock '{symbol.upper()}' added.")

    if not df.empty:
        st.markdown("### Edit / Delete Stock Holdings")
        selected_index = st.selectbox("Select stock to edit/delete", df.index, format_func=lambda i: df.at[i, "Stock Symbol"])
        if selected_index is not None:
            selected_stock = df.loc[selected_index]
            with st.form("edit_stock_form"):
                new_symbol = st.text_input("Stock Symbol", value=selected_stock["Stock Symbol"], max_chars=10)
                new_shares = st.number_input("Shares", min_value=0.0, value=float(selected_stock["Shares"]), format="%.4f")
                new_price = st.number_input("Price per Share", min_value=0.0, value=float(selected_stock["Price"]), format="%.4f")
                col1, col2 = st.columns(2)
                with col1:
                    save_btn = st.form_submit_button("Save Changes")
                with col2:
                    delete_btn = st.form_submit_button("Delete Stock")
                if save_btn:
                    if not new_symbol.strip():
                        st.error("Stock Symbol cannot be empty.")
                    elif not validate_positive_number(new_shares, "Shares") or not validate_positive_number(new_price, "Price"):
                        pass
                    else:
                        st.session_state.stocks_df.at[selected_index, "Stock Symbol"] = new_symbol.strip().upper()
                        st.session_state.stocks_df.at[selected_index, "Shares"] = new_shares
                        st.session_state.stocks_df.at[selected_index, "Price"] = new_price
                        st.session_state.stocks_df.at[selected_index, "Total Value"] = new_shares * new_price
                        save_data()
                        st.success("Stock holding updated.")
                if delete_btn:
                    st.session_state.stocks_df = df.drop(selected_index).reset_index(drop=True)
                    save_data()
                    st.success("Stock holding deleted.")

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

def main():
    st.set_page_config(page_title="Personal Finance Dashboard", layout="wide", initial_sidebar_state="expanded")
    st.title("📊 Personal Finance Dashboard")

    load_data()

    tabs = st.tabs(["Overview", "Bank Accounts", "Mutual Funds", "Stock Holdings", "Udhari Tracker"])

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

    st.markdown("---")
    st.caption("Developed with ❤️ using Streamlit")

if __name__ == "__main__":
    main()

