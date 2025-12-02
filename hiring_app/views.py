import json
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render

import pdfplumber
from io import BytesIO

# from jd_agent import analyze_job_description
# from ranker_agent import get_top_matches_for_role
# from resume_agent import process_resume_text


def index(request):
    # Serve the pre-built static index.html
    print("Index view accessed")
    return HttpResponse("Hello")


@csrf_exempt
@require_POST
def init_db(request):
    try:
        # Run migrations using the project's DB initializer
        from django.core.management import call_command
        call_command('init_db')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'status': 'ok', 'message': 'migrations run'})


def _extract_pdf_text(contents: bytes) -> str:
    with pdfplumber.open(BytesIO(contents)) as pdf:
        return "\n".join([page.extract_text() or "" for page in pdf.pages])


@csrf_exempt
@require_POST
def analyze_jd_pdf(request):
    file = request.FILES.get('file')
    job_id = request.POST.get('job_id')
    source_url = request.POST.get('source_url')
    if not file:
        return JsonResponse({'error': 'file required'}, status=400)

    if not file.name.lower().endswith('.pdf'):
        return JsonResponse({'error': 'Only PDF supported'}, status=400)

    contents = file.read()
    raw_jd_text = _extract_pdf_text(contents)
    if not raw_jd_text.strip():
        return JsonResponse({'error': 'no text extracted'}, status=400)

    try:
        memory_json = analyze_job_description(
            raw_jd_text=raw_jd_text,
            job_id=job_id,
            source_url=source_url,
            created_by='jd_analyzer_agent_pdf',
        )
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse(memory_json)


@csrf_exempt
@require_POST
def upload_resumes(request):
    files = request.FILES.getlist('files')
    source_url = request.POST.get('source_url')
    if not files:
        return JsonResponse({'error': 'no files uploaded'}, status=400)

    results = []
    for file in files:
        filename = file.name
        if not filename.lower().endswith('.pdf'):
            results.append({'file_name': filename, 'status': 'skipped', 'reason': 'not a PDF'})
            continue
        try:
            contents = file.read()
            raw_text = _extract_pdf_text(contents).strip()
            if not raw_text:
                results.append({'file_name': filename, 'status': 'error', 'reason': 'no text extracted'})
                continue
            processed = process_resume_text(raw_text=raw_text, source_url=source_url, file_name=filename)
            resume_id = processed.get('resume_id')
            parsed = processed.get('parsed', {})
            results.append({
                'file_name': filename,
                'status': 'ok',
                'resume_id': resume_id,
                'candidate_name': parsed.get('candidate_name'),
                'current_title': parsed.get('current_title'),
            })
        except Exception as e:
            results.append({'file_name': filename, 'status': 'error', 'reason': str(e)})

    return JsonResponse({'count': len(results), 'items': results})


@csrf_exempt
@require_POST
def get_top_matches_by_role(request):
    role_name = request.POST.get('role_name')
    top_k = int(request.POST.get('top_k', 3))
    if not role_name:
        return JsonResponse({'error': 'role_name required'}, status=400)
    try:
        matches = get_top_matches_for_role(role_name=role_name, top_k=top_k)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'role_name': role_name, 'top_k': top_k, 'matches': matches})
