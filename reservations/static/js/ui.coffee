window.App =
	monthData: []
	defaults: {}

	init: () ->
		@calendar = new Calendar($("#calendar"))
		new Month(@calendar.month + 1, @calendar.year)
		new Reservation(@calendar.year)
		new Holidays(@calendar.year)

	renderTime: () ->
		now = new Date()
		hh = now.getHours();
		nn = "0" + now.getMinutes()
				
		$('.time').html(
			hh + ":" + nn.substr(-2)
		);

		# Update time
		setTimeout(App.renderTime, 500)


class AjaxModel
	url: "model_url"
	constructor: (data=null) ->
		$.ajax(
			url: @url
			data: data
			success: @successHandler
			error: @errorHandler
		)

	successHandler: (data) ->
		@data = data

	errorHandler: (data) ->
		console.log("ERROR during fetching " + @url)
		console.log(data)


class Holidays extends AjaxModel
	url: "holidays"
	constructor: (@year) ->
		super(data={year: @year})

	successHandler: (data) ->
		@data = data
		lengthBefore = App.calendar._holidays.length
		for elem in data.holidays
			elem.date = new Date(elem.date * 1000)
			App.calendar.addHoliday(elem)

		if App.calendar._holidays.length != lengthBefore
			# Calendar re-render if something changed
			App.calendar.render()

class Month
	data: {}
	constructor: (@month, @year) ->
		# Retrive month data from server
		that = @
		$.ajax(
			url: 'month/' + @month + '/' + @year
			success: (data) -> that.successHandler.call(that, data)
			error: @errorHandler
		)

	successHandler: (data) ->
		for elem in data
			date = new Date(elem.fields.date * 1000)
			date.setHours(0)
			App.monthData[date] = elem.fields
		App.calendar.render()

	errorHandler: (data) ->
		console.log("ERROR during fetching user data!")
		console.log(data)

class Reservation
	constructor: (@year) ->
		# Rertive user reservations for year
		$.ajax(
			url: 'reservation'
			data: 
				year: @year
			success: @successHandler
			error: @errorHandler
		)

	successHandler: (data) ->
		@data = data
		lengthBefore = App.calendar._reservations.length
		for elem in data.reservations
			elem.date = new Date(elem.date * 1000)
			App.calendar.addReservation(elem)

		if App.calendar._reservations.length != lengthBefore
			# Calendar re-render if something changed
			App.calendar.render()

	errorHandler: (data) ->
		console.log("ERROR during fetching user reservations!")
		console.log(data)

class Calendar
	constructor: (@elem) ->
		@tableHeader = @elem.find('> thead:last')
		@tableBody = @elem.find('> tbody:last')
		now = new Date()
		@month = now.getMonth()
		@year = now.getFullYear()
		@modalInfo = $('#modal-info')
		@modalDetail = $('#modal-detail-form')

	updateReservationDay: (reservationDay) ->
		date = new Date(reservationDay.fields.date * 1000)
		date.setHours(0)
		App.monthData[date] = reservationDay.fields

	_reservations: []
	_holidays: []

	addReservation: (date) ->
		@_reservations.push(date)

	addHoliday: (holiday) ->
		@_holidays.push(holiday)

	removeReservation: (reservation_id) ->
		index = 0
		while index < @_reservations.length
			remove = (@_reservations[index].id == reservation_id)
			if remove
				@_reservations.splice(index, 1)
			else
				index += 1

	inReservations: (day, month, year) ->
		for elem in @_reservations
			if elem.date.getDate() == day and elem.date.getMonth() == month and elem.date.getFullYear() == year
				return true
		return false

	getReservations: (day, month, year) ->
		out = []
		for elem in @_reservations
			if elem.date.getDate() == day and elem.date.getMonth() == month and elem.date.getFullYear() == year
				out.push(elem)
		return out

	daysInMonth: (month, year) ->
		return new Date(year, month, 0).getDate()

	makeReservation: (mon, dayOfMonth, extraData=null) ->
		that = @
		data =
			year: mon.getFullYear()
			month: mon.getMonth() + 1
			day: dayOfMonth
			csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val()
		$.ajax(
			url: 'reservation'
			type: 'POST'
			data: $.param(data) + if extraData then "&" + extraData else ""
			success: (data) -> that.reservationSuccess.call(that, data)
			error: (data) -> that.reservationError.call(that, data)
		)

	renderDays: (mon) ->
		# Clear 
		@tableBody.empty()
		# Get some important days
		now = new Date()
		fdom = mon.getDay() - 1 # First day of month
		if fdom < 0
			fdom = 7 + fdom

		mwks = 6 # Weeks in month
		# Render days
		dayOfMonth = 0
		first = 0
		last = 0
		i = 0
		daysInMonth = @daysInMonth(mon.getMonth() + 1, mon.getFullYear())
		while i >= last
			_html = ""
			for weekDay in [0...Data.weekDays.length]
				divClass = []
				message = ""
				id = ""
				currdate = new Date(mon.getFullYear(), mon.getMonth(), dayOfMonth + 1)
				# Determine if we have reached the first day of the month
				if first >= daysInMonth
					dayOfMonth = 0
				else if (dayOfMonth > 0 and first > 0) or weekDay == fdom
					dayOfMonth += 1
					first +=1
				
				# Get last day of month
				if 1 * dayOfMonth == daysInMonth
					last = daysInMonth
		
				# Check Holidays schedule
				for holiday in @_holidays
					if holiday.date.getTime() == currdate.getTime()
						divClass.push("holiday")
						message = holiday.name
				
				# Set class
				in_future = () ->
					if (dayOfMonth > now.getDate() and \
							now.getMonth() == mon.getMonth() and \
							now.getFullYear() == mon.getFullYear() ) or \
							now.getMonth() < mon.getMonth() or \
							now.getFullYear() < mon.getFullYear()
						return true
					return false

				if divClass.length == 0
					if @inReservations(dayOfMonth, mon.getMonth(), mon.getFullYear())
						divClass.push("reservation")
					if dayOfMonth == now.getDate() and \
							now.getMonth() == mon.getMonth() and \
							now.getFullYear() == mon.getFullYear()
						divClass.push("today")
					else if weekDay in [5, 6]
						divClass.push("weekend")
					else if in_future()
						if not App.monthData[currdate] or App.monthData[currdate].spots_free > 0
							divClass.push("future")
					else
						divClass.push("past")

				# Set ID
				id = "cell_" + i + "" + weekDay + "" + (if dayOfMonth > 10 then dayOfMonth else "0" + dayOfMonth)
				
				# Render HTML
				if dayOfMonth == 0
					_html += '<td>&nbsp;</td>'
				else if message.length > 0
					_html += '<td class="' + divClass.join(" ") + '" id="'+id+'">' + dayOfMonth
					_html += '<br/><span class="content">'+message+'</span></td>'
				else
					_html += '<td class="' + divClass.join(" ") + '" id="'+id+'">' + dayOfMonth
					dayReservations = @getReservations(dayOfMonth, mon.getMonth(), mon.getFullYear())
					if "future" in divClass and (not App.defaults.reservations_limit or dayReservations.length < App.defaults.reservations_limit)
						_html += '<br/><ul class="day-actions"><li><button class="btn btn-primary btn-reserve">' + Data.label.reserve + '</button></li></ul>'
					if "reservation" in divClass and in_future()
						for reservation in dayReservations
							_html += '<br/><ul class="day-actions"><li><button db-id="' + reservation.id + '" class="btn btn-warning btn-unreserve">[' + reservation.short_desc + "] " + Data.label.cancel + '</button></li></ul>'

					if ("reservation" in divClass or "future" in divClass) and in_future()
						if App.monthData[currdate]
							spots_free = App.monthData[currdate].spots_free
						else
							spots_free = App.defaults.spots_free
						_html += '<div class="info">' + spots_free + ' ' + Data.txt.free_spots + '</div></td>'
				
			
			
			_html = "<tr>" +_html+ "</tr>";
			@tableBody.append(_html);
			that = @
			$('.btn-reserve').unbind('click').bind('click', () ->
				# Get day from ID
				dayOfMonth =  $(this).closest("td").attr("id").substr(-2)
				# Do we need to collect extra data from user?
				if App.defaults.get_extra_data
					that.clearErrors('')
					that.modalDetail.modal()
					$('.btn-primary', that.modalDetail).unbind('click').bind('click', () ->
						that.makeReservation(mon, dayOfMonth, $("form", that.modalDetail).serialize())
					)
				else
					that.makeReservation(mon, dayOfMonth)
			)

			$('.btn-unreserve').unbind('click').bind('click', () ->
				# Get day from ID
				dayOfMonth =  $(this).closest("td").attr("id").substr(-2)
				
				params =
					id: $(this).attr("db-id")
				$.ajax(
					url: 'reservation?' + $.param(params)
					type: 'DELETE'
					headers:
						"X-CSRFToken": $("input[name=csrfmiddlewaretoken]").val()
					success: (data) -> that.unreservationSuccess.call(that, data)
					error: (data) -> that.unreservationError.call(that, data)
				)
			)
			i += 1

	clearErrors: (defaultClass="success") ->
		# Clear old errors
		for element in document.getElementsByClassName("control-group")
			element.classList.remove("error")
			if defaultClass
				element.classList.add(defaultClass)
		for element in document.getElementsByClassName("help-inline")
			element.innerHTML = ""

	renderError: (fieldName, text) ->
		# Find the field
		field = document.getElementById("id_" + fieldName)
		# Check field is already wrapped with Bootstrap DOM structure
		container = field.parentNode.parentNode
		error_desc = container.getElementsByClassName("help-inline")[0]
		error_desc.innerHTML = text
		container.classList.remove("success")
		container.classList.add("error")

	reservationSuccess: (data) ->
		# Detailed reservation validation errors
		if "errors" of data
			@clearErrors()
			for error in data.errors
				@renderError(error[0], error[1])
		else
			# Update reservation day and add reservation
			@updateReservationDay(data.reservation_day)
			reservation = data.reservation
			reservation.date = new Date(reservation.date * 1000)
			@addReservation(reservation)
			# Close modal if is being used
			@modalDetail.modal('hide')
			# Repaint
			App.calendar.render()

	reservationError: (data) ->
		# Show alert with message
		$('h3', @modalInfo).text(Data.txt.operation_forbidden)
		$('p', @modalInfo).text(data.responseText)
		@modalInfo.modal('show')

	unreservationSuccess: (data) ->
		# Update reservation day and remove reservation
		@updateReservationDay(data.reservation_day)
		@removeReservation(data.id)
		# Repaint
		App.calendar.render()

	unreservationError: (data) ->
		# Show alert with message
		$('h3', @modalInfo).text(Data.txt.operation_forbidden)
		$('p', @modalInfo).text(data.responseText)
		@modalInfo.modal('show')

	renderDaysOfWeek: () ->
		# Clear first
		@tableHeader.empty()
		# Render Days of Week
		for j in [0...Data.weekDays.length]
			_html += "<th>" + Data.weekDays[j] + "</th>"
		_html = "<tr>" + _html + "</tr>"
		@tableHeader.append(_html)

	# Render whole calendar
	render: (mm=null, yy=null) ->
		now = new Date()
		# Default (now)
		if mm != null and yy != null
			@month = mm
			@year = yy

		mm = @month
		yy = @year

		# create viewed date object
		mon = new Date(yy, mm, 1)
		yp = mon.getFullYear()
		yn = mon.getFullYear()

		$('#last').removeClass('disabled')
		if now.getMonth() > mm-1 and now.getFullYear() == yy
			$('#last').addClass('disabled')

		prv = new Date(yp, mm - 1, 1)
		nxt = new Date(yn, mm + 1, 1)
	
		# Render Month
		$('.year').html(mon.getFullYear())
		$('.month').html(Data.months[mon.getMonth()])
		
		# Clear view
		@renderDaysOfWeek()
		@renderDays(mon)

		
		$('#last').unbind('click').bind('click', () ->
			if not $(this).hasClass("disabled")
				App.calendar.render(prv.getMonth(), prv.getFullYear())
				new Month(prv.getMonth() + 1, prv.getFullYear())
		)
		
		$('#current').unbind('click').bind('click', () ->
			App.calendar.render(now.getMonth(), now.getFullYear())
		)
		
		$('#next').unbind('click').bind('click', () ->
			App.calendar.render(nxt.getMonth(), nxt.getFullYear())
			new Month(nxt.getMonth() + 1, nxt.getFullYear())
		)
		
# Load
$(document).ready(() ->
	# Initialize
	App.init()
	# Render the calendar
	App.calendar.render()
	App.renderTime()
)
