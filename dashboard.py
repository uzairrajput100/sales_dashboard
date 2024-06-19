import pandas as pd
import plotly
import plotly.express as px
import streamlit as st
import os
import warnings
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

st.set_page_config(page_title="Sales Progress Dashboard", page_icon=":bar_chart:", layout="wide")
st.divider()
st.title("Sales Progress Dashboard")
st.markdown('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)
st.markdown("""
This dashboard allows you to upload your sales data and visualize various metrics. 
Upload your file using the sidebar, and the sales performance will be displayed along with other insightful charts.
You can order one for your business and customize as per your requirements.
""")
cmap = plt.get_cmap('RdYlGn')

# Make upload button
fl = st.file_uploader(":file_folder: Upload a file", type=(["csv", "xlsx", "xls"]))
if fl is not None:
    st.write(fl.name)
    file_extension = os.path.splitext(fl.name)[1]

    if file_extension == '.csv':
        df = pd.read_csv(fl, encoding="ISO-8859-1")
    elif file_extension in ['.xlsx', '.xls']:
        df = pd.read_excel(fl)
    else:
        st.error("Unsupported file type! Please upload a CSV or Excel file.")

    col1, col2 = st.columns((2))
    df["Order Date"] = pd.to_datetime(df["Order Date"])

    # Min and Max date selection
    startdate = df["Order Date"].min()
    enddate = df["Order Date"].max()

    with col1:
        date1 = st.date_input('Start Date', startdate)
    with col2:
        date2 = st.date_input('End Date', enddate)

    df = df[(df["Order Date"] >= pd.to_datetime(date1)) & (df["Order Date"] <= pd.to_datetime(date2))]

    st.sidebar.header("Choose your filter: ")
    region = st.sidebar.multiselect('Pick your Region', df['Region'].unique())

    if not region:
        df2 = df.copy()
    else:
        df2 = df[df['Region'].isin(region)]

    # Same for state
    state = st.sidebar.multiselect('Pick your State', df2['State'].unique())

    if not state:
        df3 = df2.copy()
    else:
        df3 = df2[df2['State'].isin(state)]

    # Same for city
    city = st.sidebar.multiselect('Pick your City', df3['City'].unique())

    if not region and not city and not state:
        filtered_df = df
    elif not state and not city:
        filtered_df = df[df["Region"].isin(region)]
    elif not region and not city:
        filtered_df = df[df["State"].isin(state)]
    elif state and city:
        filtered_df = df3[df3["State"].isin(state) & df3["City"].isin(city)]
    elif region and city:
        filtered_df = df3[df3["Region"].isin(region) & df3["City"].isin(city)]
    elif region and state:
        filtered_df = df3[df3["Region"].isin(region) & df3["State"].isin(state)]
    elif city:
        filtered_df = df3[df3["City"].isin(city)]
    else:
        filtered_df = df3[df3["Region"].isin(region) & df3["State"].isin(state) & df3["City"].isin(city)]

    category_df = filtered_df.groupby(by=["Category"], as_index=False)["Sales"].sum()

    with col1:
        st.subheader("Category wise Sales")
        fig = px.bar(category_df, x="Category", y="Sales", text=['${:,.2f}'.format(x) for x in category_df['Sales']],
                     template="seaborn")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Region wise Sales")
        fig = px.pie(filtered_df, values="Sales", names="Region", hole=0.5)
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    cl1, cl2 = st.columns(2)
    with cl1:
        with st.expander("Category_Viewdata"):
            st.write("Displaying styled DataFrame")
            try:
                styled_category_df = category_df.style.background_gradient(cmap=cmap)
                st.dataframe(styled_category_df.to_html(), unsafe_allow_html=True)
            except Exception as e:
                st.write(f"An error occurred: {e}")
            csv = category_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Data", data=csv, file_name="Category.csv", mime='text/csv',
                               help="Click here to download the Csv file")

    with cl2:
        with st.expander("Region_Viewdata"):
            region_df = filtered_df.groupby(by=["Region"], as_index=False)["Sales"].sum()
            try:
                styled_region_df = region_df.style.background_gradient(cmap=cmap)
                st.dataframe(styled_region_df.to_html(), unsafe_allow_html=True)
            except Exception as e:
                st.write(f"An error occurred: {e}")
            csv = region_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Data", data=csv, file_name="Region.csv", mime='text/csv',
                               help="Click here to download the Csv file")

    filtered_df["month_year"] = filtered_df["Order Date"].dt.to_period("M")
    st.subheader('Time Series Analysis')

    linechart = pd.DataFrame(filtered_df.groupby(filtered_df["month_year"].dt.strftime("%Y : %b"))["Sales"].sum()).reset_index()
    fig2 = px.line(linechart, x="month_year", y="Sales", labels={"Sales": "Amount"}, height=500, width=800, template="gridon")
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("View Data of TimeSeries"):
        st.write(linechart.T.style.background_gradient(cmap=cmap))
        csv = linechart.to_csv(index=False).encode("utf-8")
        st.download_button("Download Data", data=csv, file_name="TimeSeries.csv", mime="text/csv")

    st.subheader("Hierarchical view of Sales using TreeMap")
    fig3 = px.treemap(filtered_df, path=["Region", "Category", "Sub-Category"], values="Sales", hover_data=["Sales"],
                      color="Sub-Category")
    fig3.update_layout(width=800, height=650)
    st.plotly_chart(fig3, use_container_width=True)

    chart1, chart2 = st.columns((2))
    with chart1:
        st.subheader("Segment wise Sales")
        fig = px.pie(filtered_df, values="Sales", names="Segment", template="plotly_dark")
        fig.update_traces(textposition="inside")
        st.plotly_chart(fig, use_container_width=True)

    with chart2:
        st.subheader("Category wise Sales")
        fig = px.pie(filtered_df, values="Sales", names="Category", template="gridon")
        fig.update_traces(textposition="inside")
        st.plotly_chart(fig, use_container_width=True)

    import plotly.figure_factory as ff
    st.subheader(":point_right: Month wise Sub-Category Sales summary")
    with st.expander("Summary_Table"):
        df_sample = df[0:5][["Region", "State", "City", "Category", "Sales", "Profit", 'Quantity']]
        fig = ff.create_table(df_sample, colorscale="Cividis")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("Month wise Sub-Category Table")
        filtered_df["month"] = filtered_df["Order Date"].dt.month_name()
        sub_category_year = pd.pivot_table(data=filtered_df, values="Sales", index=["Sub-Category"], columns="month")
        st.write(sub_category_year.style.background_gradient(cmap=cmap))

    data1 = px.scatter(filtered_df, x="Sales", y="Profit", size="Quantity", title="Relationship between Sales and Profit using Scatter Plot")
    st.plotly_chart(data1, use_container_width=True)
