import matplotlib.pyplot
from .models import User, Product, Order
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")

plt = matplotlib.pyplot

from io import BytesIO

class Visualize:

    def __init__(self):
        pass

    @staticmethod
    def generate_new_old_customers_graph(dates_for_chart1: list, values_for_new_customers: list, values_for_returning_customers: list) -> BytesIO:
        
        plt.figure(figsize=(10, 5))
        plt.plot(dates_for_chart1, values_for_new_customers, label="New Customers", color="#FF9900")
        plt.plot(dates_for_chart1, values_for_returning_customers, label="Returning Customers", color="green")
        plt.xlabel('Date')
        plt.xticks(dates_for_chart1[::10], rotation=45)
        plt.gcf().autofmt_xdate()
        plt.ylabel('People')
        plt.title('New Customers and Returning Customers')
        plt.grid(True)
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()

        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()

        return img

    @staticmethod
    def generate_revenue_overtime_graph(dates:list, revenue:list) -> BytesIO:
        plt.figure(figsize=(12, 5))  # Adjust figure size for better readability
        plt.plot(dates, revenue, label="Revenue", color="green")
        plt.xticks(dates[::10])  # Keep every 10th date for better spacing
        plt.gcf().autofmt_xdate()  # Automatically format and rotate dates
        plt.xlabel('Date')
        plt.ylabel('Revenue')
        plt.title('Revenue Over Time')
        plt.tight_layout()  # Adjust layout to avoid clipping

        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()

        return img
        
    @staticmethod
    def generate_order_status_graph(statuses: list, values: list) -> BytesIO:
        plt.pie(values, labels=statuses, autopct='%1.1f%%', startangle=140, wedgeprops={'width': 0.65})
        plt.title('Order Status Distribution')
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        return img

    @staticmethod
    def generate_inventory_stocks_graph(products: list, stocks: list, xlabel = "Category", ylabel = "Stock") -> BytesIO:
        n =  len(products)
        plt.figure(figsize=(max(10, min(15, 8 + 0.2 * n)), max(5, min(12, 4 + 0.3 * n))))
        plt.bar(products, stocks, color="#11FF33")
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title('Inventory Stock Levels')
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        return img
    
    @staticmethod
    def generate_finantial_overview_graph(dates: list, expenses: list, revenue:list):
        n = min(len(expenses), len(revenue))
        if len(expenses)==n:
            revenue = revenue[:n]
        else:
            expenses = expenses[:n]

        profits = [revenue[i]-expenses[i] for i in range(n)]

        plt.figure(figsize=(10, 5))
        plt.plot(dates, expenses, label="Expenses", color="grey")
        plt.plot(dates, revenue, label="Revenue", color="green")
        plt.plot(dates, profits, label="Profits", color="pink")
        plt.xlabel('Dates')
        plt.gcf().autofmt_xdate()
        plt.ylabel('Amount')
        plt.title('Financial Performance')
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
        plt.xticks(dates[::max(1, len(dates) // 10)], rotation=45)
        
        plt.tight_layout()

        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        return img
    
    @staticmethod
    def user_role_distribution_graph(roles: list, count: list):
        plt.figure(figsize=(10, 5))
        plt.bar(roles, count, color="#009900")
        plt.title('Types of users')
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        return img

    @staticmethod 
    def generate_state_order_distribution_graph(states: list, count: list):
        n =  len(states)
        plt.figure(figsize=(20, 5+(n//10)))
        plt.barh(states, count, color="#00FF00")
        plt.title("States and Orders")
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        return img

if __name__ == "__main__":
    ...