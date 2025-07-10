"""Export API routes"""
from flask import Blueprint, request, send_file, jsonify
from io import BytesIO
import logging

from app.services.export_service import ExportService
from app.services.pdf_service import PDFService
from app.models import db, MonthlyReport, Company, TrendAnalysis

logger = logging.getLogger(__name__)

export_bp = Blueprint('export', __name__)
export_service = ExportService()
pdf_service = PDFService()


@export_bp.route('/api/export/companies', methods=['GET'])
def export_companies():
    """Export companies data"""
    try:
        format_type = request.args.get('format', 'csv')
        filters = {
            'sector': request.args.get('sector'),
            'trend': request.args.get('trend'),
            'min_market_cap': request.args.get('min_market_cap', type=float)
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # Generate export
        data = export_service.export_companies_data(format_type, filters)
        
        # Create response
        mimetype_map = {
            'csv': 'text/csv',
            'json': 'application/json',
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        extension_map = {
            'csv': 'csv',
            'json': 'json',
            'excel': 'xlsx'
        }
        
        return send_file(
            BytesIO(data),
            mimetype=mimetype_map.get(format_type, 'text/plain'),
            as_attachment=True,
            download_name=f'companies_export.{extension_map.get(format_type, "txt")}'
        )
        
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@export_bp.route('/api/export/company/<ticker>/timeline', methods=['GET'])
def export_company_timeline(ticker):
    """Export company sentiment timeline"""
    try:
        format_type = request.args.get('format', 'csv')
        
        # Generate export
        data = export_service.export_company_timeline(ticker, format_type)
        
        # Create response
        mimetype_map = {
            'csv': 'text/csv',
            'json': 'application/json',
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        extension_map = {
            'csv': 'csv',
            'json': 'json',
            'excel': 'xlsx'
        }
        
        return send_file(
            BytesIO(data),
            mimetype=mimetype_map.get(format_type, 'text/plain'),
            as_attachment=True,
            download_name=f'{ticker}_timeline.{extension_map.get(format_type, "txt")}'
        )
        
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@export_bp.route('/api/export/market-summary', methods=['GET'])
def export_market_summary():
    """Export market summary data"""
    try:
        format_type = request.args.get('format', 'json')
        
        # Generate export
        data = export_service.export_market_summary(format_type)
        
        # Create response
        mimetype_map = {
            'json': 'application/json',
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        extension_map = {
            'json': 'json',
            'excel': 'xlsx'
        }
        
        return send_file(
            BytesIO(data),
            mimetype=mimetype_map.get(format_type, 'application/json'),
            as_attachment=True,
            download_name=f'market_summary.{extension_map.get(format_type, "json")}'
        )
        
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@export_bp.route('/api/export/transcript/<int:transcript_id>', methods=['GET'])
def export_transcript(transcript_id):
    """Export a specific transcript with analysis"""
    try:
        format_type = request.args.get('format', 'json')
        
        # Generate export
        data = export_service.export_transcript(transcript_id, format_type)
        
        # Create response
        mimetype_map = {
            'json': 'application/json',
            'pdf': 'application/pdf'
        }
        
        extension_map = {
            'json': 'json',
            'pdf': 'pdf'
        }
        
        return send_file(
            BytesIO(data),
            mimetype=mimetype_map.get(format_type, 'application/json'),
            as_attachment=True,
            download_name=f'transcript_{transcript_id}.{extension_map.get(format_type, "json")}'
        )
        
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@export_bp.route('/api/export/monthly-report/<int:report_id>/pdf', methods=['GET'])
def export_monthly_report_pdf(report_id):
    """Export monthly report as PDF"""
    try:
        # Get report
        report = MonthlyReport.query.get_or_404(report_id)
        
        # Generate PDF
        pdf_data = pdf_service.generate_monthly_report_pdf(report)
        
        return send_file(
            BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'OpalSight_Monthly_Report_{report.report_date.strftime("%Y_%m")}.pdf'
        )
        
    except Exception as e:
        logger.error(f"PDF export error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@export_bp.route('/api/export/company/<ticker>/report/pdf', methods=['GET'])
def export_company_report_pdf(ticker):
    """Export company analysis report as PDF"""
    try:
        # Get company
        company = Company.query.filter_by(ticker=ticker).first_or_404()
        
        # Get recent trend analyses
        trends = TrendAnalysis.query.filter_by(company_id=company.id)\
            .order_by(TrendAnalysis.analysis_date.desc())\
            .limit(5)\
            .all()
        
        # Generate PDF
        pdf_data = pdf_service.generate_company_report_pdf(company, trends)
        
        return send_file(
            BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{ticker}_Sentiment_Analysis_Report.pdf'
        )
        
    except Exception as e:
        logger.error(f"PDF export error: {str(e)}")
        return jsonify({'error': str(e)}), 500 