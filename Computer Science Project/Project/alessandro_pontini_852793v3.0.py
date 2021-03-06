#!/usr/bin/env python
# coding: utf-8

# #   <span style="color:#5F9EA0">Progetto Python Alessandro Pontini Matricola: 852793</span>

# ***

# In[1]:


# importo librerie
import pandas as pd
import datetime
import numpy as np
pd.options.mode.chained_assignment = None


# In[2]:


# scrivo directory
dire_df_lenders_not_normalized = '/Users/alessandropontini/Documents/db/progetto_python/additional-kiva-snapshot/loans_lenders.csv'
dire_df_loans = '/Users/alessandropontini/Documents/db/progetto_python/additional-kiva-snapshot/loans.csv'
dire_df_lenders_info = '/Users/alessandropontini/Documents/db/progetto_python/additional-kiva-snapshot/lenders.csv'
dire_df_country_stat = '/Users/alessandropontini/Documents/db/progetto_python/additional-kiva-snapshot/country_stats.csv'


# ***

# ##  <span style="color:red">1) Normalize the loan_lenders table. In the normalized table, each row must have one loan_id and one lender.</span>

# ***

# In[3]:


# leggo il file csv
df_lenders_not_normalized = pd.read_csv(dire_df_lenders_not_normalized)


# In[4]:


df_lenders_not_normalized.head()


# In[5]:


# impongo index=loan_id per poter usare explode che per ogni loan_id mi prende ogni elemento della lista creata con la strip 
# e mi crea un nuove righe in un nuovo data set
df_lenders_normalized = df_lenders_not_normalized.set_index('loan_id')['lenders'].str.split(pat=',').explode().reset_index()


# In[6]:


# mostro risultato
df_lenders_normalized.head()


# ***

# ##  <span style="color:red">2) For each loan, add a column duration corresponding to the number of days between the disburse time and the planned expiration time. If any of those two dates is missing, also the duration must be missing.</span>

# ***

# In[7]:


# leggo il file loans, ma per la quantità di dati che devo leggere
# preferisco leggere le date come tali e non come stringhe.
df_loans = pd.read_csv(dire_df_loans, parse_dates=['disburse_time', 'planned_expiration_time'])


# In[8]:


# ci sono delle date che non hanno disburse_time > planned_expiration_time, non ha senso un prestito che si estingue
# prima della data di sborso, perciò controllo se ce ne sono e in effetti si ci sono.
# creo un df che li contiene df_temp
temp_df = df_loans.loc[df_loans['disburse_time'] > df_loans['planned_expiration_time']]


# In[9]:


temp_df[['disburse_time', 'planned_expiration_time']]


# In[10]:


# inverto i valori
# # https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy vedere soluzione qua

temp_df['temp_date'] = temp_df.disburse_time 
temp_df.disburse_time = temp_df.planned_expiration_time
temp_df.planned_expiration_time = temp_df.temp_date
del temp_df['temp_date']


# In[11]:


temp_df[['disburse_time', 'planned_expiration_time']]


# In[12]:


# uso funzione isin per vedere i loan_id che coincidano e cambio df_loan con i nuovi di df_temp corretti
df_loans.loc[df_loans.loan_id.isin(temp_df.loan_id), ['disburse_time', 'planned_expiration_time']] = temp_df[['disburse_time','planned_expiration_time']]


# In[13]:


# sono stati invertiti
df_loans.loc[df_loans['disburse_time'] > df_loans['planned_expiration_time']]


# In[14]:


# creo una colonna per la duration e faccio differenza, dopo di che mostro il risultato
df_loans['duration'] = df_loans['planned_expiration_time'] - df_loans['disburse_time']
df_loans[['loan_id','duration']]


# ***

# ## <span style="color:red">3) Find the lenders that have funded at least twice.</span>

# ***

# In[15]:


temp_df = df_loans[['loan_id', 'status', 'loan_amount']]


# In[16]:


# trovo df che mi serve per punto 3 in temp_df
# trovo df2 che mi da' il totale del lent per i punti successivi
temp_df2 = df_lenders_not_normalized.merge(temp_df, how='left', left_on='loan_id', right_on='loan_id')
# ci sono 4 valori null
temp_df2 = temp_df2.fillna(0)
total_lent = temp_df2.loan_amount.sum()
temp_df = df_lenders_normalized.merge(temp_df, how='left', left_on='loan_id', right_on='loan_id')


temp_df = temp_df.loc[temp_df.status == 'funded']
temp_df = temp_df.groupby('lenders').size().reset_index(name='count').sort_values(by='count', ascending=False)

temp_df.loc[temp_df['count'] >= 2]


# ***

# ## <span style="color:red">4) For each country, compute how many loans have involved that country as borrowers.</span>
# 

# ***

# In[17]:


# suppongo che in loans che country_code identifichi le nazionalità delle persone perciò con una groupby posso raggrupparle
# e con una size so il numero presente per ogni nazione
df_loans.groupby('country_code').size()


# ***

# ## <span style="color:red"> 5) For each country, compute the overall amount of money borrowed.</span>

# ***

# In[18]:


# raggruppo in base allo stato di appartenenza scegliendo di mostrare la colonna loan_amount e sommo i risultati.
df_loans.groupby('country_code')['loan_amount'].sum()


# ***

# ## <span style="color:red">6) Like the previous point, but expressed as a percentage of the overall amount lent.</span>

# ***

# In[19]:


# uso il total_lent calcolato in precedenza
df_loans.groupby('country_code')['loan_amount'].sum()/total_lent*100


# ***

# ## <span style="color:red">7) Like the three previous points, but split for each year (with respect to disburse time).</span>

# ***

# In[20]:


temp_df = df_loans[['disburse_time', 'country_code', 'loan_amount']]
temp_df.disburse_time = temp_df['disburse_time'].dt.tz_localize(None).dt.year


# In[21]:


# vedo quante persone all'anno punto 4
temp_df.groupby(['country_code','disburse_time']).size()


# In[22]:


# faccio le somme punto 5
temp_df.groupby(['country_code','disburse_time'])['loan_amount'].sum()


# In[23]:


# uso total_lent precedente
temp_df.groupby(['country_code', 'disburse_time'])['loan_amount'].sum()/total_lent*100


# ***

# ## <span style="color:red">8) For each lender, compute the overall amount of money lent.</span>

# ***

# In[24]:


# uso un df temporaneo per immagazzinare la join tra df_lenders_normalized e df_loans con solo i campi loan_id
# e loan_amount che usero per i conti successivamente
temp_df = df_lenders_normalized.merge(df_loans[['loan_id', 'loan_amount']], how='left', on='loan_id')


# In[25]:


# salvo in un df temp 2 il raggruppamento secondo count, per contare il numero totale di ogni loan id
temp_df2 = temp_df.groupby('loan_id')['lenders'].count().reset_index().rename(columns={"lenders": "tot_num_lender"})


# In[26]:


# faccio ultima merge per avere nel mio data set accanto alla colonna di loan id la colonna dei lenders_y
# che corrisponde al mio count
temp_df = temp_df.merge(temp_df2, how='left', on='loan_id')


# In[27]:


temp_df


# In[28]:


# creo nuova colonna per segnare le singole quote per ogni loan_id
temp_df['single_amount']= temp_df['loan_amount']/temp_df['tot_num_lender']


# In[29]:


# ora raggruppo per ogni lender
temp_df.groupby('lenders')['single_amount'].sum()


# ***

# ## <span style='color:red'> 9) For each country, compute the difference between the overall amount of money lent and the overall amount of money borrowed. Since the country of the lender is often unknown, you can assume that the true distribution among the countries is the same as the one computed from the rows where the country is known.</span>

# ***

# ## Problema di fondo che abbiamo trovato che il data set estremamente scarno con molti NULL, perciò dovevamo distribuire i soldi borrowed amolti valori NULL. Personalmento ho optato per la distribuzione del totale loan_amount dei null secondo percentuali di nazionalità ottenute da diverse join con la informazione sicura che avevo cioè i dati dei lenders. 

# ***

# In[30]:


# inizio aggiungendo ai miei dataset anche le informazioni dei lenders_info
df_lenders_info = pd.read_csv(dire_df_lenders_info)


# In[31]:


# merge in una temporanea di df_lenders con la normalizzata 
# per avere loan_id
temp_df = df_lenders_info[['permanent_name', 'country_code']].merge(df_lenders_normalized, how='left', left_on='permanent_name', right_on='lenders')


# In[32]:


# temp_df2 contiene tutte le righe in cui lenders è presente in loan e non ha lenders == null
temp_df2 = temp_df.dropna(subset=['lenders'])


# In[33]:


# contiene tutti i borrowed
temp_df3 = temp_df.loc[temp_df.lenders.isna()]


# In[34]:


# analizzando il temp df 3 mi accorgo che ho qualche country code ma non ho nessun loan amount
# per tanto decido di non eseguire altri compiti su questo subdf
temp_df3


# In[35]:


temp_df2


# In[36]:


# aggiungiamo anche la colonna loan_amount per avere un totale dei lenders/loan/country ( potrebbero esserci dei NULL)
temp_df2=temp_df2.merge(df_loans[['loan_id', 'loan_amount']],how='left',on='loan_id')


# In[37]:


temp_df2.info()


# In[38]:


# metto i null a 0 di loan amount che sono 4
temp_df2['loan_amount'] = temp_df2['loan_amount'].fillna(0)


# In[39]:


# inizio controllando quelli con country valore che esiste, perdo quasi 3000000 righe
df_lenders_loans_country = temp_df2.dropna(subset=['country_code'])


# In[40]:


df_lenders_loans_country = df_lenders_loans_country.groupby('country_code')['loan_amount'].sum()


# In[41]:


total_lent = df_lenders_loans_country.sum()


# In[42]:


df_lenders_loans_country = df_lenders_loans_country.reset_index()


# In[43]:


# cosi facendo ho percentuale del totale per ogni country che è il punto che mi serve
df_lenders_loans_country['percentage'] = round(df_lenders_loans_country['loan_amount']/total_lent,10)


# In[44]:


df_lenders_loans_country


# In[45]:


temp_df2 = temp_df2.loc[temp_df2.country_code.isna()]


# In[46]:


temp_df2


# In[47]:


total_amount = temp_df2.loan_amount.sum()


# In[48]:


total_amount


# In[49]:


# li moltiplico per la percentuale dei country che conosco lenders e poi li sommo con i precedenti
x = total_amount * df_lenders_loans_country.percentage

df_lenders_loans_country['total_lenders_amount_with_no_country'] = x


# In[50]:


df_lenders_loans_country['total_lent'] = df_lenders_loans_country.loan_amount + df_lenders_loans_country.total_lenders_amount_with_no_country


# In[51]:


df_lenders_loans_country


# In[52]:


# no duplicates
df_loans.duplicated()


# In[53]:


temp_df = df_loans.groupby('country_code')['loan_amount'].sum()


# In[54]:


temp_df = temp_df.reset_index()


# In[55]:


temp_df


# In[56]:


del df_lenders_loans_country['total_lenders_amount_with_no_country']


# In[57]:


df_lenders_loans_country = df_lenders_loans_country.merge(temp_df,how='left', on='country_code')


# In[58]:


df_lenders_loans_country


# In[59]:


df_lenders_loans_country.loan_amount_y = df_lenders_loans_country.loan_amount_y.fillna(0)


# In[60]:


df_lenders_loans_country['lent_borrowed'] = df_lenders_loans_country.total_lent - df_lenders_loans_country.loan_amount_y


# In[61]:


df_lenders_loans_country


# ***

# ## <span style='color:red'>10) Which country has the highest ratio between the difference computed at the previous point and the population?</span>

# ***

# In[62]:


# importo data set che necessito
df_country_stat = pd.read_csv(dire_df_country_stat)


# In[63]:


temp_df = df_country_stat.groupby('country_code')['population'].sum()


# In[64]:


temp_df = temp_df.reset_index()


# In[65]:


df_lenders_loans_country = df_lenders_loans_country.merge(temp_df,how='left', on='country_code')


# In[66]:


# se ho popolazione nan metto il primo quartile
first_quantile = df_lenders_loans_country.population.quantile(0.25)
df_lenders_loans_country.population = df_lenders_loans_country.population.fillna(first_quantile)


# In[67]:


df_lenders_loans_country


# In[68]:


#calcolo percentuale su i lent-borrowed e la popolazione, successivamente trovo l'idmax per la percentuale che mi dice essere CANADA
df_lenders_loans_country['percentage'] = round(df_lenders_loans_country['lent_borrowed']/df_lenders_loans_country['population']*100, 2)
#temp_df3=temp_df3.reset_index()


# In[69]:


max_ratio = df_lenders_loans_country.loc[df_lenders_loans_country['percentage'].idxmax()]
min_ratio = df_lenders_loans_country.loc[df_lenders_loans_country['percentage'].idxmin()]


# In[70]:


print(max_ratio,'\n',min_ratio)


# ***

# ## <span style='color:red'>11) Which country has the highest ratio between the difference computed at point 9 and the population that is not below the poverty line?</span>

# ***

# In[71]:


temp_df2 = df_country_stat.groupby('country_code')[['country_code','population','population_below_poverty_line']].head(175)


# In[72]:


temp_df2['population_below_poverty_line'] = temp_df2['population_below_poverty_line']/100


# In[73]:


temp_df2.country_code = temp_df2.country_code.fillna('NA')


# In[74]:


temp_df2.info()


# In[75]:


mean = temp_df2.population_below_poverty_line.mean()
temp_df2.population_below_poverty_line = temp_df2.population_below_poverty_line.fillna(mean)


# In[76]:


temp_df2['population_below_poverty_line'] = temp_df2['population'] - (temp_df2['population_below_poverty_line']*temp_df2['population'])


# In[77]:


temp_df2 = temp_df2.merge(df_lenders_loans_country[['country_code', 'lent_borrowed']], left_on='country_code', right_on='country_code')


# In[78]:


mean = temp_df2.lent_borrowed.mean()
temp_df2.lent_borrowed = temp_df2.lent_borrowed.fillna(mean)


# In[79]:


temp_df2['percentage_poverty'] = round(temp_df2['lent_borrowed']/temp_df2['population_below_poverty_line']*100, 2)


# In[80]:


max_ratio = temp_df2.loc[temp_df2['percentage_poverty'].idxmax()]
min_ratio = temp_df2.loc[temp_df2['percentage_poverty'].idxmin()]


# In[81]:


print(max_ratio,'\n',min_ratio)


# ***

# ## <span style='color:red'>12) For each year, compute the total amount of loans. Each loan that has planned expiration time and disburse time in different years must have its amount distributed proportionally to the number of days in each year. For example, a loan with disburse time December 1st, 2016, planned expiration time January 30th 2018, and amount 5000USD has an amount of 5000USD * 31 / (31+365+30) = 363.85 for 2016, 5000USD * 365 / (31+365+30) = 4284.04 for 2017, and 5000USD * 30 / (31+365+30) = 352.11 for 2018.</span>

# ***

# ### Decido di eliminare tutte le colonne con NaN, in particolar modo tutte le colonne che non presentano disburse_time oppure planned_expiration_time

# ***

# In[82]:


temp_df = df_loans[['disburse_time', 'planned_expiration_time', 'loan_amount', 'duration']].dropna()


# In[83]:


temp_df['disburse_time']= temp_df['disburse_time'].dt.tz_localize(None)
temp_df['planned_expiration_time']= temp_df['planned_expiration_time'].dt.tz_localize(None)


# In[84]:


temp_df['differenza'] = (temp_df.planned_expiration_time.dt.year) - (temp_df.disburse_time.dt.year)


# In[85]:


temp_df.groupby('differenza').size()


# In[86]:


# tengo solo i giorni
temp_df.duration = temp_df.duration.dt.days


# In[87]:


temp_df.duration


# In[88]:


# aggiungo colonna anno, mese,giorno per comodità
temp_df['day_disburse_time'] = temp_df.disburse_time.dt.strftime("%d")
temp_df.day_disburse_time = temp_df.day_disburse_time.astype('int')
temp_df['day_planned_expiration_time'] = temp_df.planned_expiration_time.dt.strftime("%d")
temp_df.day_planned_expiration_time = temp_df.day_planned_expiration_time.astype('int')

temp_df['month_disburse_time'] = temp_df.disburse_time.dt.strftime("%m")
temp_df.month_disburse_time = temp_df.month_disburse_time.astype('int')


temp_df['year_disburse_time'] = temp_df.disburse_time.dt.strftime("%Y")
temp_df['year_planned_expiration_time'] = temp_df.planned_expiration_time.dt.strftime("%Y")
temp_df.year_disburse_time = temp_df.year_disburse_time.astype('int')
temp_df.year_planned_expiration_time = temp_df.year_planned_expiration_time.astype('int')


# In[101]:


lista_final = []
def func_final(df):
    # dichiaro la mia lista risultato finale
    ok = 'ok'
    global lista_final
    # calcolo il planned_expiration_time - i giorni dal 1-1-dell'anno preso in considerazione
    lim_inf = datetime.datetime(df.year_planned_expiration_time, 1,1)
    day_inf = df.planned_expiration_time - lim_inf
    day_inf = day_inf.days
    
    # calcolo i giorni dal 31-12-dell'anno preso in considerazione - i disburse_time
    lim_sup = datetime.datetime(df.year_disburse_time, 12, 31)
    day_sup = lim_sup - df.disburse_time
    day_sup = day_sup.days
    
    # controllo che non vadano elementi uguali 0 al divisore caso limite per cui o disburse o planned uguali ai limiti
    if day_inf == 0:
        day_inf = 1
    
    if day_sup == 0:
        day_sup = 1
    
    # calcolo quanti giorni per gli anni servono
    year_operation = (365*df.differenza) - 365
    
    # calcolo gli anni 2012 e 2016 bisestili
    q = range(df.year_disburse_time, df.year_planned_expiration_time)
    
    if 2016 in q == True and year_operation > 0:
        year_operation = year_operation+1
    elif 2012 in q == True and year_operation > 0:
        year_operation = year_operation+1
    
    flag = df.year_disburse_time
    
    # calcolo quanti giorni per gli anni servono
    divisor = day_inf+day_sup+year_operation

    
    if df.disburse_time.year == df.planned_expiration_time.year:
        money = df.loan_amount
        years = df.year_disburse_time
        result = [money,years]
        lista_final.append(result)
        
    else:
        while df.year_planned_expiration_time != flag:
            # calcolo per ogni anno  la quota partendo dal disburse
            money_day = df.loan_amount * day_sup
            money = safe_division(money_day,divisor)
            result = [money,flag]
            lista_final.append(result)
            
            # bisestile
            if flag == 2016 or flag == 2012:
                day_sup = 366
            else :
                day_sup = 365
                
            flag = flag + 1  
            
            
    # calcolo i restanti giorni
        money_day = df.loan_amount * day_inf
        money = safe_division(money_day, divisor)
        years = df.year_planned_expiration_time
        result = [money,years]
        lista_final.append(result)
     
    return ok

def create_df_year(array):
    d1 = {'tot' : array}
    df2 = pd.DataFrame(d1)
    df3 = df2.tot.apply(pd.Series)
    df3.columns = ['total', 'year'] 
    return df3

def safe_division(a, b):
    if not b:
        return 0
    return a / b


# In[102]:


temp_df.apply(lambda x : func_final(x), axis=1)


# In[103]:


final_df = create_df_year(lista_final)


# In[104]:


final_df.year = final_df.year.astype('int')
final_df.total = final_df.total.astype('int')
final_df.groupby('year').sum()

