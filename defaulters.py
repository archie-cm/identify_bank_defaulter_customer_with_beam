import apache_beam as beam

# for datetime manipulation
from datetime import datetime

p = beam.Pipeline()

def calculate_points(element):

  customer_id, first_name, last_name, realtionship_id, card_type, max_limit, spent, cash_withdrawn,payment_cleared,payment_date = element.split(',')
  #[CT28383,Miyako,Burns,R_7488,Issuers,500,490,38,101,30-01-2018]
  
  spent = int(spent)    # spent = 490
  payment_cleared = int(payment_cleared)   #payment_cleared = 101
  max_limit = int(max_limit)               # max_limit = 500
  
  key_name = customer_id + ', ' + first_name + ' ' + last_name     # key_name = CT28383,Miyako Burns
  defaulter_points = 0
  
  # payment_cleared is less than 70% of spent - give 1 point
  if payment_cleared < (spent * 0.7): 
     defaulter_points += 1                                                # defaulter_points =  1 
 
  # spend is = 100% of max limit and any amount of payment is pending
  if (spent == max_limit) and (payment_cleared < spent): 
     defaulter_points += 1                                                # defaulter_points =  2
   
  if (spent == max_limit) and (payment_cleared < (spent*0.7)): 
     defaulter_points += 1                                                # defaulter_points = 3
                                  
  return key_name, defaulter_points                                     # {CT28383,Miyako Burns  3}

def format_result(sum_pair):
  key_name, points = sum_pair
  return str(key_name) + ', ' + str(points) + ' fraud_points'  

def calculate_late_payment(elements):               # [CT88330,Humberto,Banks,Serviceman,LN_1559,Medical Loan,26-01-2018,2000,30-01-2018]
  
  due_date = datetime.strptime(elements[6].rstrip().lstrip(), '%d-%m-%Y')           # due_date = 26-01-2018
  payment_date = datetime.strptime(elements[8].rstrip().lstrip(), '%d-%m-%Y')       # payment_date = 30-01-2018
  
  if payment_date <= due_date:
    elements.append('0') 
  else:
    elements.append('1')                           # [CT88330,Humberto,Banks,Serviceman,LN_1559,Medical Loan,26-01-2018,2000,30-01-2018,1]
    
  return elements

def format_output(sum_pair):
  key_name, miss_months = sum_pair
  return str(key_name) + ', ' + str(miss_months) + ' missed'

def calculate_month(input_list):        #input  [CT88330,Humberto,Banks,Serviceman,LN_1559,Medical Loan,26-01-2018, 2000, 30-01-2018]
                                       
  # Convert payment_date to datetime and extract month of payment
  payment_date = datetime.strptime(input_list[8].rstrip().lstrip(), '%d-%m-%Y')  # payment_date = 30-01-2018
  input_list.append(str(payment_date.month))                                     # [CT88330,Humberto,Banks,Serviceman,LN_1559,Medical Loan,26-01-2018, 2000, 30-01-2018, 01]
  
  return input_list 

def calculate_personal_loan_defaulter(input):       #input key -> CT68554,Ronald Chiki   value --> [01,05,06,07,08,09,10,11,12]
    max_allowed_missed_months = 4
    max_allowed_consecutive_missing = 2
    
    name, months_list = input                                   # [CT68554,Ronald,Chiki,Serviceman,LN_8460,Personal Loan,25-01-2018,50000,25-01-2018]
      
    months_list.sort()
    sorted_months = months_list                                 # sorted_months = [01,05,06,07,08,09,10,11,12]
    total_payments = len(sorted_months)                         # total_payments = 10
    
    missed_payments = 12 - total_payments                       # missed_payments = 2

    if missed_payments > max_allowed_missed_months:             # false
       return name, missed_payments                             #  N/A
    
    consecutive_missed_months = 0

    temp = sorted_months[0] - 1                                 # temp = 0
    if temp > consecutive_missed_months:                        # false
        consecutive_missed_months = temp                        #NA

    temp = 12 - sorted_months[total_payments-1]                  
    if temp > consecutive_missed_months:
        consecutive_missed_months = temp                        # temp = 0

    for i in range(1, len(sorted_months)):                      # [01,05,06,07,08,09,10,11,12]
        temp = sorted_months[i] - sorted_months[i-1] -1         # temp = 5-1-1 = 3
        if temp > consecutive_missed_months:
            consecutive_missed_months = temp                    # consecutive_missed_months = 3
    
    if consecutive_missed_months > max_allowed_consecutive_missing:
       return name, consecutive_missed_months                   # CT68554,Ronald Chiki   3
    
    return name, 0 

def return_tuple(element):
  thisTuple=element.split(',')
  return (thisTuple[0],thisTuple[1:])    

card_defaulter = (
                  p
                  | 'Read credit card data' >> beam.io.ReadFromText('cards.txt',skip_header_lines=1)
                  | 'Calculate defaulter points' >> beam.Map(calculate_points)                            
                  | 'Combine points for defaulters' >> beam.CombinePerKey(sum)                            # key--> CT28383,Miyako Burns   value --> 6 
                  | 'Filter card defaulters' >> beam.Filter(lambda element: element[1] > 0)
                  | 'Format output' >> beam.Map(format_result)                                            # CT28383,Miyako Burns,6 fraud_points
                 # | 'Write credit card data' >> beam.io.WriteToText('outputs/card_skippers') 
                  | 'tuple ' >> beam.Map(return_tuple)  
                  )		

medical_loan_defaulter = (
                            p
                            |  beam.io.ReadFromText('loan.txt',skip_header_lines=1)   # 1stRow--> CT88330,Humberto,Banks,Serviceman,LN_1559,Medical Loan,26-01-2018, 2000, 30-01-2018
                            | 'Split Row' >> beam.Map(lambda row : row.split(','))
                            | 'Filter medical loan' >> beam.Filter(lambda element : (element[5]).rstrip().lstrip() == 'Medical Loan')
                            | 'Calculate late payment' >> beam.Map(calculate_late_payment)
                            | 'Make key value pairs' >> beam.Map(lambda elements: (elements[0] + ', ' + elements[1]+' '+elements[2], int(elements[9])) ) 
                            | 'Group medical loan based on month' >> beam.CombinePerKey(sum)                       # key--> (CT88330,Humberto Banks)  value --> 7
                            | 'Check for medical loan defaulter' >> beam.Filter(lambda element: element[1] >= 3)
                            | 'Format medical loan output' >> beam.Map(format_output)      # CT88330,Humberto Banks,7 missed
                         )     

personal_loan_defaulter = (
                            p
                            | 'Read' >> beam.io.ReadFromText('loan.txt',skip_header_lines=1)   
                            | 'Split' >> beam.Map(lambda row : row.split(','))
                            | 'Filter personal loan' >> beam.Filter(lambda element : (element[5]).rstrip().lstrip() == 'Personal Loan')
                            | 'Split and Append New Month Column' >> beam.Map(calculate_month)   
                            | 'Make key value pairs loan' >> beam.Map(lambda elements: (elements[0] + ', ' + elements[1]+' '+elements[2], int(elements[9])) ) 
                            | 'Group personal loan based on month' >> beam.GroupByKey()                                  # CT68554,Ronald Chiki [01,05,06,07,08,09,10,11,12]
                            | 'Check for personal loan defaulter' >> beam.Map(calculate_personal_loan_defaulter)          # CT68554,Ronald Chiki   3
                            | 'Filter only personal loan defaulters' >> beam.Filter(lambda element: element[1] > 0)
                            | 'Format personal loan output' >> beam.Map(format_output)        # CT68554,Ronald Chiki,3 missed
                          )   
                          
final_loan_defaulters = (
                          ( personal_loan_defaulter, medical_loan_defaulter )
                          | 'Combine all defaulters' >> beam.Flatten()
                          #| 'Write all defaulters to text file' >> beam.io.WriteToText('outputs/loan_defaulters')
                          | 'tuple for loan' >> beam.Map(return_tuple)
                        )  
                        
both_defaulters =  (
                    {'card_defaulter': card_defaulter, 'loan_defaulter': final_loan_defaulters}
                    | beam.CoGroupByKey()
                    |'Write p3 results' >> beam.io.WriteToText('outputs/both')
                   )            

				  		  
p.run()	
