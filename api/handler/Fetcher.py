import pandas as pd
from api.models import *
from django.utils import timezone
from urllib.parse import urlparse


class Fetcher:
    def __init__(self):
        pass
    
    def clean_url(self,url):
        base_url = url.split("?")[0].replace("/edit","")
        extension = '/export?gid={0}&format=csv'
        if "gid=" in url:   
            parsed = urlparse(url)
            val = ""
            for q in parsed.query.split("&"):
                if "gid" in q:
                    val = q.split("=")[-1]
                    break
            new_url = base_url + extension.format(val)
        else:
            new_url = base_url + extension.format("0")
        return new_url

    def get_data_from_google_sheet(self,url):
        df = pd.read_csv(url, delimiter=",", encoding="utf-8")
        return df

    def extract_data(self,url):
        new_url = self.clean_url(url)
        df = self.get_data_from_google_sheet(new_url)
        return df

    def clean_data(self,df):
        df.fillna(0, inplace=True)
        df["Open Time ET"] = pd.to_datetime(df["Open Time ET"])
        df["Closed Time ET"] = pd.to_datetime(df["Closed Time ET"])
        df["DD Time ET"] = pd.to_datetime(df["DD Time ET"])
        return df

    def analyze_data(self, df, initial_amount, risk_free_rate=0):
        df['Cumulative P/L'] = df['trade_pl'].cumsum()
        df['Cumulative Max'] = df['Cumulative P/L'].cummax()
        df['Drawdown'] = df['Cumulative P/L'] - df['Cumulative Max']

        total_pl = float(df['trade_pl'].sum())
        absolute_sum_pl = float(df['trade_pl'].abs().sum())
        annual_return_percentage = (total_pl / initial_amount) * 100 
        max_drawdown = float(df['Drawdown'].min())
        max_drawdown_percentage = (max_drawdown / absolute_sum_pl) * 100
        total_trades = len(df)

        # Win trades calculation
        win_trades = df[df['trade_pl'] > 0]
        win_percentage = len(win_trades) / total_trades * 100
        number_of_win_trades = len(win_trades)

        # Profit Factor calculation
        profit_factor = float(win_trades['trade_pl'].sum()) / float(abs(df[df['trade_pl'] < 0]['trade_pl'].sum()))

        # Monthly P/L calculation
        df['month'] = df['closed_time_et'].dt.to_period('M')
        monthly_pl = df.groupby('month')['trade_pl'].sum()
        monthly_pl_dict = {str(period): float(pl) for period, pl in monthly_pl.items()}

        # Winning months calculation
        winning_months = len(monthly_pl[monthly_pl > 0])

        # Calculate today's P&L
        today = pd.to_datetime('today').normalize()
        try:
            todays_pl = df[df['closed_time_et'].dt.normalize() == today]['trade_pl'].sum()
        except:
            todays_pl = 0
        df['trade_pl'] = df['trade_pl'].astype(float)
        # Sharpe Ratio calculation
        mean_return = float(df['trade_pl'].mean())
        std_return = float(df['trade_pl'].std())  # Convert to float
        sharpe_ratio = (mean_return - float(risk_free_rate)) / std_return if std_return != 0 else 0

        # Sortino Ratio calculation
        downside_std = df[df['trade_pl'] < 0]['trade_pl'].std()
        downside_std = float(downside_std)  # Convert to float
        sortino_ratio = (mean_return - float(risk_free_rate)) / downside_std if downside_std != 0 else 0

        # Prepare the context to pass to the template
        context = {
            'annual_return_percentage': annual_return_percentage,
            'max_drawdown_percentage': max_drawdown_percentage,
            'total_trades': total_trades,
            'win_percentage': win_percentage,
            'number_of_win_trades': number_of_win_trades,
            'profit_factor': profit_factor,
            'winning_months': winning_months,
            'monthly_pl': monthly_pl_dict,
            'todays_pl': todays_pl,
            'sharpe_ratio': sharpe_ratio,  # New metric
            'sortino_ratio': sortino_ratio,  # New metric
        }

        return context
    
    def execute(self, url, initial_amount, strat):
        df = self.extract_data(url)
        df = self.clean_data(df)

        # Add new trades to the Trade model
        for _, row in df.iterrows():
            Trade.objects.update_or_create(
                strategy=strat,
                closed_time_et=row['Closed Time ET'],
                defaults={
                    'open_time_et': row['Open Time ET'],
                    'side': row['Side'],
                    'qty_open': row['Qty Open'],
                    'symbol': row['Symbol'],
                    'descrip': row['Descrip'],
                    'avg_price_open': row['Avg Price Open'],
                    'qty_closed': row['Qty Closed'],
                    'avg_price_closed': row['Avg Price Closed'],
                    'dd_as_percentage': row.get('DD as %', None),
                    'dd_dollars': row.get('DD $', None),
                    'dd_time_et': row.get('DD Time ET', None),
                    'dd_quant': row.get('DD Quant', None),
                    'dd_worst_price': row.get('DD Worst Price', None),
                    'trade_pl': row['Trade P/L'],
                }
            )

        # Analyze the updated trades
        trades = Trade.objects.all().values()
        df = pd.DataFrame(trades)
        context = self.analyze_data(df, initial_amount)

        today = timezone.now().date()
        # Check if a Result object for today already exists
        result, created = Result.objects.get_or_create(
            strategy=strat,
            date=today,
            defaults={
                'annual_return_percentage': context['annual_return_percentage'],
                'max_drawdown_percentage': context['max_drawdown_percentage'],
                'total_trades': context['total_trades'],
                'win_percentage': context['win_percentage'],
                'profit_factor': context['profit_factor'],
                'winning_months': context['winning_months'],
                'monthly_pl': context['monthly_pl'],
                'todays_pl': context['todays_pl'],
                'sharpe_ratio': context['sharpe_ratio'],  # New metric
                'sortino_ratio': context['sortino_ratio'],  # New metric
                'win_trades' : context['number_of_win_trades']
            }
        )

        # If the Result object already exists, update its values
        if not created:
            result.annual_return_percentage = context['annual_return_percentage']
            result.max_drawdown_percentage = context['max_drawdown_percentage']
            result.total_trades = context['total_trades']
            result.win_percentage = context['win_percentage']
            result.profit_factor = context['profit_factor']
            result.winning_months = context['winning_months']
            result.monthly_pl = context['monthly_pl']
            result.todays_pl = context['todays_pl']
            result.sharpe_ratio = context['sharpe_ratio']  # Update Sharpe Ratio
            result.sortino_ratio = context['sortino_ratio']  # Update Sortino Ratio
            result.win_trades = context['number_of_win_trades']
            result.save()

       