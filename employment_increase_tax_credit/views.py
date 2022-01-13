from django.shortcuts import render
from django.http import HttpResponse

import datetime
import numpy as np
from dateutil.relativedelta import relativedelta
import pandas as pd
from io import BytesIO as IO

from .forms import DateForm, UploadFileForm

def index(request):
    if request.method == 'POST':
        date_form = DateForm(request.POST)
        upload_file_form = UploadFileForm(request.POST, request.FILES)
        if date_form.is_valid() and upload_file_form.is_valid():
            cd = date_form.cleaned_data
            business_start_date = cd['date']

            download_excel_file = calculate_employee(request.FILES['file'], business_start_date)

            response = HttpResponse(download_excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', )
            response['Content-Disposition'] = 'attachment; filename=result.xlsx'

            return response
    
    else:
        date_form = DateForm(initial={'date': '2017-01-01'})
        upload_file_form = UploadFileForm()

    return render(request, 'employment_increase_tax_credit/index.html', {'date_form': date_form, 'upload_file_form': upload_file_form})

def last_day_of_month(day):
    next_month = day.replace(day=28) + datetime.timedelta(days=4)
    return next_month - datetime.timedelta(days=next_month.day)

def calculate_age(birthday, today):
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

def calculate_employee(excel_file, business_start_date):
    df = pd.read_excel(excel_file, converters={'생년월일': np.datetime64, '입사일자': np.datetime64, '퇴사일자': np.datetime64})
        
    df['군복무개월수'] = df['군복무개월수'].fillna(0)
    df['장애인및상이자'] = df['장애인및상이자'].fillna('X')
    df['518민주화운동부상자및고엽제후유의증환자'] = df['518민주화운동부상자및고엽제후유의증환자'].fillna('X')
    df['월소정60시간이상근무단시간근로자'] = df['월소정60시간이상근무단시간근로자'].fillna('X')

    end_year = 2021

    start_year = max(2017, business_start_date.year)
    if start_year >= 2017:
        start_month = business_start_date.month
    else:
        start_month = 1

    for index, value in df['생년월일'].items():
        df.loc[index, '입사일나이'] = calculate_age(df.loc[index, '생년월일'], df.loc[index, '입사일자'])

    for year in range(start_year, end_year + 1):
        if year > start_year:
            start_month = 1

        for month in range(start_month, 13):
            date = last_day_of_month(datetime.date(year, month, 1))

            for index, value in df['생년월일'].items():
                if df.loc[index, '군복무개월수'] > 0:
                        # 군복무는 6년을 한도로 연령에서 차감함.
                    value = df.loc[index, '생년월일'] + relativedelta(months = min(df.loc[index, '군복무개월수'], 72))
                df.loc[index, '병역차감나이'] = calculate_age(value, date)
                
            year_month_string = str(year) + '-' + str(month)

            # 중도퇴사자의 경우 매월 상시근로자수 계산 시 말일 퇴사자는 해당 월의 상시근로자수에 포함, 말일 전 퇴사자는 제외. (홈택스 상담사례 '고용 증대' 2019-03-05)
            df.loc[((df['입사일자'] <= pd.Timestamp(date)) & ((df['퇴사일자'] >= pd.Timestamp(date)) | df['퇴사일자'].isnull())) & (df['근무지'] == '수도권'), year_month_string] = '일반(수도권)'
            df.loc[((df['입사일자'] <= pd.Timestamp(date)) & ((df['퇴사일자'] >= pd.Timestamp(date)) | df['퇴사일자'].isnull())) & (df['근무지'] == '지방'), year_month_string] = '일반(지방)'
            # 29세 이하. 단시간 근로자는 제외
            df.loc[(df[year_month_string] == '일반(수도권)') & (df['병역차감나이'] <= 29) & (df['월소정60시간이상근무단시간근로자'] == 'X'), year_month_string] = '청년등(수도권)'
            df.loc[(df[year_month_string] == '일반(지방)') & (df['병역차감나이'] <= 29) & (df['월소정60시간이상근무단시간근로자'] == 'X'), year_month_string] = '청년등(지방)'
            # 장애인, 상이자
            df.loc[(df[year_month_string] == '일반(수도권)') & (df['장애인및상이자'] != 'X'), year_month_string] = '청년등(수도권)'
            df.loc[(df[year_month_string] == '일반(지방)') & (df['장애인및상이자'] != 'X'), year_month_string] = '청년등(지방)'
            # 518민주화운동부상자, 고엽제후유의증환자 (2019년 1월 1일 이후 개시하는 과세연도 분부터 적용)
            if year >= 2019:
                df.loc[(df[year_month_string] == '일반(수도권)') & (df['518민주화운동부상자및고엽제후유의증환자'] != 'X'), year_month_string] = '청년등(수도권)'
                df.loc[(df[year_month_string] == '일반(지방)') & (df['518민주화운동부상자및고엽제후유의증환자'] != 'X'), year_month_string] = '청년등(지방)'
            # 근로계약 체결일 현재 연령이 60세 이상인 사람
            if year >= 2021:
                df.loc[(df[year_month_string] == '일반(수도권)') & (df['입사일나이'] >= 60), year_month_string] = '청년등(수도권)'
                df.loc[(df[year_month_string] == '일반(지방)') & (df['입사일나이'] >= 60), year_month_string] = '청년등(지방)'
            
    df_summary = pd.DataFrame(index=['청년등근로자수합계(수도권)', '청년등근로자수합계(지방)', '청년등근로자수합계(전체)', '일반근로자수합계(수도권)', '일반근로자수합계(지방)', '일반근로자수합계(전체)', '총상시근로자수합계(수도권)', '총상시근로자수합계(지방)', '총상시근로자수합계(전체)', '개월수', '청년등근로자수(수도권)', '청년등근로자수(지방)', '청년등근로자수(전체)', '일반근로자수(수도권)', '일반근로자수(지방)', '일반근로자수(전체)', '총상시근로자수(수도권)', '총상시근로자수(지방)', '총상시근로자수(전체)'], columns=range(start_year, end_year + 1)).fillna(0)

    for index in df:
        if '-' not in index:
            continue

        df.loc['청년등근로자수(수도권)', index] = df.loc[(df[index] == '청년등(수도권)') & (df['월소정60시간이상근무단시간근로자'] == 'X'), index].count()
        df.loc['청년등근로자수(지방)', index] = df.loc[(df[index] == '청년등(지방)') & (df['월소정60시간이상근무단시간근로자'] == 'X'), index].count()
        # 15세 이상 29세 이하인 사람 중 단시간 근로자는 청년등에서 제외하나 근로계약 체결일 현재 연령이 60세 이상인 사람의 경우 단시간 근로자 제외 규정 없음. (조특법 제26조의7 제3항 3호)
        df.loc['청년등근로자수(수도권)', index] = df.loc['청년등근로자수(수도권)', index] + df.loc[(df[index] == '청년등(수도권)') & (df['월소정60시간이상근무단시간근로자'] == '지원X'), index].count() * 0.5
        df.loc['청년등근로자수(지방)', index] = df.loc['청년등근로자수(지방)', index] + df.loc[(df[index] == '청년등(지방)') & (df['월소정60시간이상근무단시간근로자'] == '지원X'), index].count() * 0.5
        df.loc['청년등근로자수(수도권)', index] = df.loc['청년등근로자수(수도권)', index] + df.loc[(df[index] == '청년등(수도권)') & (df['월소정60시간이상근무단시간근로자'] == '지원O'), index].count() * 0.75
        df.loc['청년등근로자수(지방)', index] = df.loc['청년등근로자수(지방)', index] + df.loc[(df[index] == '청년등(지방)') & (df['월소정60시간이상근무단시간근로자'] == '지원O'), index].count() * 0.75
        df.loc['청년등근로자수(전체)', index] = df.loc['청년등근로자수(수도권)', index] + df.loc['청년등근로자수(지방)', index]

        df.loc['일반근로자수(수도권)', index] = df.loc[(df[index] == '일반(수도권)') & (df['월소정60시간이상근무단시간근로자'] == 'X'), index].count()
        df.loc['일반근로자수(지방)', index] = df.loc[(df[index] == '일반(지방)') & (df['월소정60시간이상근무단시간근로자'] == 'X'), index].count()
        df.loc['일반근로자수(수도권)', index] = df.loc['일반근로자수(수도권)', index] + df.loc[(df[index] == '일반(수도권)') & (df['월소정60시간이상근무단시간근로자'] == '지원X'), index].count() * 0.5
        df.loc['일반근로자수(지방)', index] = df.loc['일반근로자수(지방)', index] + df.loc[(df[index] == '일반(지방)') & (df['월소정60시간이상근무단시간근로자'] == '지원X'), index].count() * 0.5
        df.loc['일반근로자수(수도권)', index] = df.loc['일반근로자수(수도권)', index] + df.loc[(df[index] == '일반(수도권)') & (df['월소정60시간이상근무단시간근로자'] == '지원O'), index].count() * 0.75
        df.loc['일반근로자수(지방)', index] = df.loc['일반근로자수(지방)', index] + df.loc[(df[index] == '일반(지방)') & (df['월소정60시간이상근무단시간근로자'] == '지원O'), index].count() * 0.75
        df.loc['일반근로자수(전체)', index] = df.loc['일반근로자수(수도권)', index] + df.loc['일반근로자수(지방)', index]

        df.loc['총상시근로자수(수도권)', index] = df.loc['청년등근로자수(수도권)', index] + df.loc['일반근로자수(수도권)', index]
        df.loc['총상시근로자수(지방)', index] = df.loc['청년등근로자수(지방)', index] + df.loc['일반근로자수(지방)', index]
        df.loc['총상시근로자수(전체)', index] = df.loc['총상시근로자수(수도권)', index] + df.loc['총상시근로자수(지방)', index]

        df_summary.loc['청년등근로자수합계(수도권)', int(index[:4])] = df_summary.loc['청년등근로자수합계(수도권)', int(index[:4])] + df.loc['청년등근로자수(수도권)', index]
        df_summary.loc['청년등근로자수합계(지방)', int(index[:4])] = df_summary.loc['청년등근로자수합계(지방)', int(index[:4])] + df.loc['청년등근로자수(지방)', index]
        df_summary.loc['청년등근로자수합계(전체)', int(index[:4])] = df_summary.loc['청년등근로자수합계(전체)', int(index[:4])] + df.loc['청년등근로자수(전체)', index]
        df_summary.loc['일반근로자수합계(수도권)', int(index[:4])] = df_summary.loc['일반근로자수합계(수도권)', int(index[:4])] + df.loc['일반근로자수(수도권)', index]
        df_summary.loc['일반근로자수합계(지방)', int(index[:4])] = df_summary.loc['일반근로자수합계(지방)', int(index[:4])] + df.loc['일반근로자수(지방)', index]
        df_summary.loc['일반근로자수합계(전체)', int(index[:4])] = df_summary.loc['일반근로자수합계(전체)', int(index[:4])] + df.loc['일반근로자수(전체)', index]
        df_summary.loc['총상시근로자수합계(수도권)', int(index[:4])] = df_summary.loc['총상시근로자수합계(수도권)', int(index[:4])] + df.loc['총상시근로자수(수도권)', index]
        df_summary.loc['총상시근로자수합계(지방)', int(index[:4])] = df_summary.loc['총상시근로자수합계(지방)', int(index[:4])] + df.loc['총상시근로자수(지방)', index]
        df_summary.loc['총상시근로자수합계(전체)', int(index[:4])] = df_summary.loc['총상시근로자수합계(전체)', int(index[:4])] + df.loc['총상시근로자수(전체)', index]
        df_summary.loc['개월수', int(index[:4])] = df_summary.loc['개월수', int(index[:4])] + 1

    for index in df_summary:
        df_summary.loc['청년등근로자수(수도권)', index] = int((df_summary.loc['청년등근로자수합계(수도권)', index] / df_summary.loc['개월수', index]) * 100) / 100
        df_summary.loc['청년등근로자수(지방)', index] = int((df_summary.loc['청년등근로자수합계(지방)', index] / df_summary.loc['개월수', index]) * 100) / 100
        df_summary.loc['청년등근로자수(전체)', index] = df_summary.loc['청년등근로자수(수도권)', index] + df_summary.loc['청년등근로자수(지방)', index]
        df_summary.loc['일반근로자수(수도권)', index] = int((df_summary.loc['일반근로자수합계(수도권)', index] / df_summary.loc['개월수', index]) * 100) / 100
        df_summary.loc['일반근로자수(지방)', index] = int((df_summary.loc['일반근로자수합계(지방)', index] / df_summary.loc['개월수', index]) * 100) / 100
        df_summary.loc['일반근로자수(전체)', index] = df_summary.loc['일반근로자수(수도권)', index] + df_summary.loc['일반근로자수(지방)', index]
        df_summary.loc['총상시근로자수(수도권)', index] = int((df_summary.loc['총상시근로자수합계(수도권)', index] / df_summary.loc['개월수', index]) * 100) / 100
        df_summary.loc['총상시근로자수(지방)', index] = int((df_summary.loc['총상시근로자수합계(지방)', index] / df_summary.loc['개월수', index]) * 100) / 100
        df_summary.loc['총상시근로자수(전체)', index] = df_summary.loc['총상시근로자수(수도권)', index] + df_summary.loc['총상시근로자수(지방)', index]

    download_excel_file = IO()
    xlwriter = pd.ExcelWriter(download_excel_file, engine='xlsxwriter')
    df.to_excel(xlwriter, '월별근로자수')
    df_summary.to_excel(xlwriter, '근로자수집계')

    xlwriter.save()
    xlwriter.close()
    download_excel_file.seek(0)

    return download_excel_file

def social_insurance(request):
    if request.method == 'POST':
        date_form = DateForm(request.POST)
        upload_file_form = UploadFileForm(request.POST, request.FILES)
        if date_form.is_valid() and upload_file_form.is_valid():
            cd = date_form.cleaned_data
            business_start_date = cd['date']

            download_excel_file = calculate_employee_for_social_insurance(request.FILES['file'], business_start_date)

            response = HttpResponse(download_excel_file.read(), content_type='application/vnd.openxmlformats-officedocumnet.spreadsheetml.sheet', )
            response['Content-Disposition'] = 'attachment; filename=result.xlsx'

            return response
    
    else:
        date_form = DateForm(initial={'date': '2017-01-01'})
        upload_file_form = UploadFileForm()

    return render(request, 'employment_increase_tax_credit/social_insurance.html', {'date_form': date_form, 'upload_file_form': upload_file_form})

def calculate_employee_for_social_insurance(excel_file, business_start_date):
    df = pd.read_excel(excel_file, converters={'생년월일': np.datetime64, '입사일자': np.datetime64, '퇴사일자': np.datetime64})
        
    df['군복무개월수'] = df['군복무개월수'].fillna(0)
    df['경력단절여성상시근로자'] = df['경력단절여성상시근로자'].fillna('X')
    df['월소정60시간이상근무단시간근로자'] = df['월소정60시간이상근무단시간근로자'].fillna('X')

    end_year = 2021

    start_year = max(2017, business_start_date.year)
    if start_year >= 2017:
        start_month = business_start_date.month
    else:
        start_month = 1

    for index, value in df['생년월일'].items():
        df.loc[index, '입사일나이'] = calculate_age(df.loc[index, '생년월일'], df.loc[index, '입사일자'])

    for year in range(start_year, end_year + 1):
        if year > start_year:
            start_month = 1

        for month in range(start_month, 13):
            date = last_day_of_month(datetime.date(year, month, 1))

            for index, value in df['생년월일'].items():
                if df.loc[index, '군복무개월수'] > 0:
                        # 군복무는 6년을 한도로 연령에서 차감함.
                    value = df.loc[index, '생년월일'] + relativedelta(months = min(df.loc[index, '군복무개월수'], 72))
                df.loc[index, '병역차감나이'] = calculate_age(value, date)
                
            year_month_string = str(year) + '-' + str(month)

            # 중도퇴사자의 경우 매월 상시근로자수 계산 시 말일 퇴사자는 해당 월의 상시근로자수에 포함, 말일 전 퇴사자는 제외. (홈택스 상담사례 '고용 증대' 2019-03-05)
            df.loc[((df['입사일자'] <= pd.Timestamp(date)) & ((df['퇴사일자'] >= pd.Timestamp(date)) | df['퇴사일자'].isnull())), year_month_string] = '일반'
            # 29세 이하. 단시간 근로자는 제외한다는 규정이 없음.
            df.loc[(df[year_month_string] == '일반') & (df['병역차감나이'] <= 29), year_month_string] = '청년등'
            # 경력단절여성 상시근로자
            df.loc[(df[year_month_string] == '일반') & (df['경력단절여성상시근로자'] == 'O'), year_month_string] = '청년등'
            
    df_summary = pd.DataFrame(index=['청년등근로자수합계', '일반근로자수합계', '총상시근로자수합계', '개월수', '청년등근로자수', '일반근로자수', '총상시근로자수'], columns=range(start_year, end_year + 1)).fillna(0)

    for index in df:
        if '-' not in index:
            continue

        df.loc['청년등근로자수', index] = df.loc[(df[index] == '청년등') & (df['월소정60시간이상근무단시간근로자'] == 'X'), index].count()
        df.loc['청년등근로자수', index] = df.loc['청년등근로자수', index] + df.loc[(df[index] == '청년등') & (df['월소정60시간이상근무단시간근로자'] == '지원X'), index].count() * 0.5
        df.loc['청년등근로자수', index] = df.loc['청년등근로자수', index] + df.loc[(df[index] == '청년등') & (df['월소정60시간이상근무단시간근로자'] == '지원O'), index].count() * 0.75

        df.loc['일반근로자수', index] = df.loc[(df[index] == '일반') & (df['월소정60시간이상근무단시간근로자'] == 'X'), index].count()
        df.loc['일반근로자수', index] = df.loc['일반근로자수', index] + df.loc[(df[index] == '일반') & (df['월소정60시간이상근무단시간근로자'] == '지원X'), index].count() * 0.5
        df.loc['일반근로자수', index] = df.loc['일반근로자수', index] + df.loc[(df[index] == '일반') & (df['월소정60시간이상근무단시간근로자'] == '지원O'), index].count() * 0.75

        df.loc['총상시근로자수', index] = df.loc['청년등근로자수', index] + df.loc['일반근로자수', index]

        df_summary.loc['청년등근로자수합계', int(index[:4])] = df_summary.loc['청년등근로자수합계', int(index[:4])] + df.loc['청년등근로자수', index]
        df_summary.loc['일반근로자수합계', int(index[:4])] = df_summary.loc['일반근로자수합계', int(index[:4])] + df.loc['일반근로자수', index]
        df_summary.loc['총상시근로자수합계', int(index[:4])] = df_summary.loc['총상시근로자수합계', int(index[:4])] + df.loc['총상시근로자수', index]

        df_summary.loc['개월수', int(index[:4])] = df_summary.loc['개월수', int(index[:4])] + 1

    for index in df_summary:
        df_summary.loc['청년등근로자수', index] = int((df_summary.loc['청년등근로자수합계', index] / df_summary.loc['개월수', index]) * 100) / 100
        df_summary.loc['일반근로자수', index] = int((df_summary.loc['일반근로자수합계', index] / df_summary.loc['개월수', index]) * 100) / 100
        df_summary.loc['총상시근로자수', index] = int((df_summary.loc['총상시근로자수합계', index] / df_summary.loc['개월수', index]) * 100) / 100

    download_excel_file = IO()
    xlwriter = pd.ExcelWriter(download_excel_file, engine='xlsxwriter')
    df.to_excel(xlwriter, '월별근로자수')
    df_summary.to_excel(xlwriter, '근로자수집계')

    xlwriter.save()
    xlwriter.close()
    download_excel_file.seek(0)

    return download_excel_file