# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta
from textwrap import dedent

from dateutil import easter

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import datetime, dateutil, safe_eval, test_python_expr


class CalendarPublicHolidayTemplateLine(models.Model):
    _name = "calendar.public.holiday.template.line"
    _description = "Calendar Public Holiday Template Line"
    _order = "date_type, date, day_offset, name"

    template_id = fields.Many2one(
        "calendar.public.holiday.template",
        "Template",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(required=True, translate=True)
    date_type = fields.Selection(
        [
            ("fixed", "Fixed Date"),
            ("easter", "Easter Sunday"),
            ("calculated", "Calculated (Python Code)"),
        ],
        required=True,
        default="fixed",
        help="Fixed Date: the day and month of the date are used every year.\n"
        "Other values: the date is calculated for every year.",
    )
    date = fields.Date(help="The year is ignored.")
    python_code = fields.Text(
        help="Python code calculating the date of the holiday, which must be "
        "assigned to the variable 'result'. Available variables:\n"
        "- year: the year the holiday is generated for\n"
        "- datetime: the datetime module\n"
        "- relativedelta: the dateutil.relativedelta module\n"
        "- easter(year): Easter Sunday of the given year\n"
        "Example: result = datetime.date(year, 11, 22) + "
        "relativedelta.relativedelta(weekday=relativedelta.WE(-1))",
    )
    day_offset = fields.Integer(
        help="Number of days added to (or subtracted from, when negative) "
        "the calculated date."
    )
    state_ids = fields.Many2many(
        "res.country.state",
        "calendar_public_holiday_template_line_state_rel",
        "template_line_id",
        "state_id",
        "Related States",
    )

    @api.constrains("date_type", "date")
    def _check_date(self):
        for line in self:
            if line.date_type != "fixed":
                continue
            if not line.date:
                raise ValidationError(
                    self.env._(
                        "A date is required for the fixed holiday %s.", line.name
                    )
                )
            if line.date.month == 2 and line.date.day == 29:
                raise ValidationError(
                    self.env._(
                        "The 29th of February cannot be used as fixed holiday (%s).",
                        line.name,
                    )
                )

    @api.constrains("date_type", "python_code")
    def _check_python_code(self):
        for line in self:
            if line.date_type != "calculated":
                continue
            if not (line.python_code or "").strip():
                raise ValidationError(
                    self.env._("Python code is required for the holiday %s.", line.name)
                )
            msg = test_python_expr(expr=dedent(line.python_code).strip(), mode="exec")
            if msg:
                raise ValidationError(msg)

    def _get_date(self, year):
        self.ensure_one()
        date = getattr(self, f"_get_date_{self.date_type}")(year)
        return date + timedelta(days=self.day_offset)

    def _get_date_fixed(self, year):
        return self.date.replace(year=year)

    def _get_date_easter(self, year):
        return easter.easter(year)

    def _get_python_eval_context(self, year):
        return {
            "year": year,
            "datetime": datetime,
            "relativedelta": dateutil.relativedelta,
            "easter": easter.easter,
        }

    def _get_date_calculated(self, year):
        context = self._get_python_eval_context(year)
        try:
            safe_eval(
                dedent(self.python_code).strip(), context, mode="exec", nocopy=True
            )
        except Exception as e:
            raise UserError(
                self.env._(
                    "Error while evaluating the python code of the "
                    "holiday %(name)s: %(error)s",
                    name=self.name,
                    error=e,
                )
            ) from e
        result = context.get("result")
        if isinstance(result, datetime.datetime):
            result = result.date()
        if not isinstance(result, datetime.date):
            raise UserError(
                self.env._(
                    "The python code of the holiday %(name)s must assign a date "
                    "to 'result', got %(result)r.",
                    name=self.name,
                    result=result,
                )
            )
        return result

    def _prepare_public_holiday_line_vals(self, public_holiday):
        self.ensure_one()
        return {
            "name": self.name,
            "date": self._get_date(public_holiday.year),
            "variable_date": self.date_type != "fixed",
            "state_ids": [(6, 0, self.state_ids.ids)],
            "public_holiday_id": public_holiday.id,
        }
