from django.shortcuts import render
from django.http import HttpResponse
from ..models import Course
from ..models import Document
from ..models import Record
import random

def index(request):

    if request.method == "POST":
        codes = ['BSCS', 'BSA', 'BSN']

        # Record.objects.create(
        #     student_number = "9999",
        #     first_name = "Set",
        #     last_name = "Vergara",
        #     course_code = random.choice(codes)        
        # )

        Document.objects.create(
            code = "AFG",
            description = "Application for Graduation",
            no_of_files = 5
        )

        return HttpResponse("Populated")
    else:
        return render(request, "dummy.html")