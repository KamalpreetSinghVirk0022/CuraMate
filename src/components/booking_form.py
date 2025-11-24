# components/booking_form.py

import streamlit as st
from services.booking_service import get_specialty_from_risks, parse_booking_request, find_and_book_appointment
from services.google_calendar_service import add_appointment_to_calendar
import re

def show_booking_form():
    """
    Displays the appointment booking form with NLP and Google Calendar integration.
    """
    
    st.subheader("Book an Appointment")
    st.warning("Your report indicates high-risk factors. We recommend booking an appointment with a specialist.")
    
    # 1. Determine the required specialty
    health_risks = st.session_state.get('health_risks_for_booking', [])
    specialty = get_specialty_from_risks(health_risks)
    
    if not specialty:
        st.error("Could not determine the required medical specialty. Please contact support.")
        if st.button("Go Back"):
            del st.session_state.show_booking_form
            st.rerun()
        return

    st.info(f"Your report suggests a consultation with a **{specialty}**.")
    
    # 2. Initialize Success State
    if 'booking_success' not in st.session_state:
        st.session_state.booking_success = False

    # 3. Get patient details from session
    user_details = st.session_state.get('user_details_for_booking', {})
    
    # --- FORM SECTION (Hidden after success) ---
    if not st.session_state.booking_success:
        with st.form("booking_form_nlp"):
            st.write("Please confirm your details and preferences:")
            
            # --- Layout: 3 Columns for Personal Info ---
            col1, col2, col3 = st.columns(3)
            with col1:
                patient_name = st.text_input("Full Name", value=user_details.get("name", ""))
            with col2:
                patient_email = st.text_input("Email", value=st.session_state.user.get("email", ""))
            with col3:
                patient_phone = st.text_input("Phone Number", placeholder="e.g., +919876543210")
            
            st.markdown("---")
            
            booking_preference = st.text_area(
                "What city and what days are you free?",
                placeholder="e.g., 'I live in Delhi and am free next Tuesday or any day next weekend.'"
            )
            
            submit_button = st.form_submit_button("Find & Book Appointment")

        if submit_button:
            # --- Form Validation ---
            if not all([patient_name, patient_email, patient_phone, booking_preference]):
                st.error("Please fill in all fields.")
                return

            with st.spinner("Analyzing your request and finding a doctor..."):
                
                # A. Parse NLP Request
                parsed_request = parse_booking_request(booking_preference)
                
                if not parsed_request:
                    return # Error is handled inside parse_function

                patient_info = {
                    "name": patient_name,
                    "email": patient_email,
                    "phone": patient_phone,
                }
                
                # B. Find & Book
                result = find_and_book_appointment(
                    specialty=specialty,
                    parsed_request=parsed_request,
                    patient_details=patient_info,
                    user_id=st.session_state.user['id']
                )

                if result["success"]:
                    # --- Success: Update State & Rerun ---
                    st.session_state.booking_success = True
                    st.session_state.booking_result = result
                    st.rerun()

                else:
                    # --- Failure: Show Alternatives ---
                    st.error(result["message"])
                    
                    if "alternatives" in result:
                        st.info(f"Here are the top-ranked specialists in {parsed_request['city']} you can contact directly:")
                        for doc in result["alternatives"][:3]: # Show top 3
                            with st.expander(f"**{doc['Name']}** - {doc['hospital/clinic']}"):
                                st.write(f"**Experience:** {doc['experience']}")
                                st.write(f"**Fee:** ₹{doc['fee']}")
                                st.write(f"**Working Days:** {doc['working days']}")
    
    # --- SUCCESS SECTION (Visible after booking) ---
    if st.session_state.booking_success:
        result = st.session_state.booking_result
        
        st.success(f"**Appointment Request Sent!**")
        st.balloons()
        
        st.markdown(f"""
        <div style="padding: 15px; border-radius: 10px; background-color: #1F2937; border: 1px solid #374151; margin-bottom: 20px;">
            <h3 style="margin-top:0; color: #3B82F6;">Booking Confirmed</h3>
            <p><strong>Doctor:</strong> {result['doctor_name']}</p>
            <p><strong>Hospital:</strong> {result['hospital']}</p>
            <p><strong>Date:</strong> {result['date']} (9:00 AM)</p>
            <hr style="border-top: 1px solid #374151;">
            <p style="font-size: 0.9em; color: #9CA3AF;">A WhatsApp confirmation has been sent to your phone.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # --- NEW: Google Calendar Button ---
        if st.button("📅 Add to Google Calendar", type="primary"):
            with st.spinner("Syncing to Google Calendar..."):
                success = add_appointment_to_calendar(
                    doctor_name=result['doctor_name'],
                    hospital=result['hospital'],
                    date_str=result['date']
                )
                
                if success:
                    st.success("Appointment added to your calendar!")
                else:
                    st.error("Failed to add to calendar. Please check your credentials.")
        # -----------------------------------
        
    # --- Navigation Footer ---
    if st.button("Go Back to Analysis"):
        # Clean up all session state flags
        del st.session_state.show_booking_form
        del st.session_state.booking_success
        if 'booking_result' in st.session_state:
            del st.session_state.booking_result
        if 'health_risks_for_booking' in st.session_state:
            del st.session_state.health_risks_for_booking
        st.rerun()




























# import streamlit as st
# from services.booking_service import get_specialty_from_risks, parse_booking_request, find_and_book_appointment
# import re



# from services.booking_service import create_calendar_file

# def show_booking_form():
#     """
#     Displays the appointment booking form with NLP.
#     """
    
#     st.subheader("Book an Appointment")
#     st.warning("Your report indicates high-risk factors. We recommend booking an appointment with a specialist.")
    
#     # 1. Determine the required specialty
#     health_risks = st.session_state.get('health_risks_for_booking', [])
#     specialty = get_specialty_from_risks(health_risks)
    
#     if not specialty:
#         st.error("Could not determine the required medical specialty. Please contact support.")
#         if st.button("Go Back"):
#             del st.session_state.show_booking_form
#             st.rerun()
#         return

#     st.info(f"Your report suggests a consultation with a **{specialty}**.")
    
#     # 2. Get patient details from session
#     user_details = st.session_state.get('user_details_for_booking', {})
    
#     if 'booking_success' not in st.session_state:
#         st.session_state.booking_success = False

#     if not st.session_state.booking_success:
#         with st.form("booking_form_nlp"):
#             st.write("Please confirm your details and preferences:")


#             col1, col2, col3 = st.columns(3)
#             with col1:
#                 patient_name = st.text_input("Full Name", value=user_details.get("name", ""))
#             with col2:
#                 patient_email = st.text_input("Email", value=st.session_state.user.get("email", ""))
#             with col3:
#                 patient_phone = st.text_input("Phone Number", placeholder="e.g., +919876543210")
            
#             # patient_name = st.text_input("Full Name", value=user_details.get("name", ""))
#             # patient_email = st.text_input("Email", value=st.session_state.user.get("email", ""))
#             # patient_phone = st.text_input("Phone Number", placeholder="e.g., +919876543210")
            
#             st.markdown("---")
            
#             booking_preference = st.text_area(
#                 "What city and what days are you free?",
#                 placeholder="e.g., 'I live in Delhi and am free next Tuesday or any day next weekend.'"
#             )
            
#             submit_button = st.form_submit_button("Find & Book Appointment")

#         if submit_button:
#             # --- Form Validation ---
#             if not all([patient_name, patient_email, patient_phone, booking_preference]):
#                 st.error("Please fill in all fields.")
#                 return

#             with st.spinner("Analyzing your request and finding a doctor..."):
                
#                 parsed_request = parse_booking_request(booking_preference)
                
#                 if not parsed_request:
#                     return

#                 patient_info = {
#                     "name": patient_name,
#                     "email": patient_email,
#                     "phone": patient_phone,
#                 }
                
#                 result = find_and_book_appointment(
#                     specialty=specialty,
#                     parsed_request=parsed_request,
#                     patient_details=patient_info,
#                     user_id=st.session_state.user['id']
#                 )

#                 if result["success"]:
                   
#                     st.session_state.booking_success = True
#                     st.session_state.booking_result = result
                    
#                     # We only rerun once here to show the success message
#                     st.rerun() 

#                 else:
#                     # --- ACTION 2: No Doctor Found, Show Alternatives ---
#                     st.error(result["message"])
                    
#                     if "alternatives" in result:
#                         st.info(f"Here are the top-ranked specialists in {parsed_request['city']} you can contact directly:")



#                         # Get the top 3 doctors
#                     top_docs = result["alternatives"][:3]
                    
#                     # Create 3 columns for our cards
#                     cols = st.columns(len(top_docs))
                    
#                     for i, doc in enumerate(top_docs):
#                         with cols[i]:
#                             # Inject our custom HTML card
#                             st.markdown(
#                                 f"""
#                                 <div class="card">
#                                     <h3>{doc['Name']}</h3>
#                                     <p>⭐ {doc['experience']}</p>
#                                     <p>💰 ₹{doc['fee']}</p>
#                                     <p>🏥 {doc['hospital/clinic']}</p>
#                                     <p>🗓️ {doc['working days']}</p>
#                                 </div>
#                                 """,
#                                 unsafe_allow_html=True
#                             )
#                         # for doc in result["alternatives"][:3]: # Show top 3
#                         #     with st.expander(f"**{doc['Name']}** - {doc['hospital/clinic']}"):
#                         #         st.write(f"**Experience:** {doc['experience']}")
#                         #         st.write(f"**Fee:** ₹{doc['fee']}")
#                         #         st.write(f"**Working Days:** {doc['working days']}")
    
#     if st.session_state.booking_success:
#         result = st.session_state.booking_result
        
#         st.success(f"**Appointment Request Sent!**")
#         st.balloons()
#         st.markdown(f"""
#         Your request for an appointment with **{result['doctor_name']}** has been submitted.
#         - **Date:** {result['date']}
#         - **Hospital:** {result['hospital']}
        
#         You will receive a WhatsApp confirmation shortly.
#         """)


        
#         # 1. Generate the .ics file content
#         ics_content = create_calendar_file(
#             doctor_name=result['doctor_name'],
#             hospital=result['hospital'],
#             date_str=result['date']
#         )
        
#         # 2. Add the download button
#         if ics_content:
#             st.download_button(
#                 label="📥 Add to Your Calendar",
#                 data=ics_content,
#                 file_name=f"Appointment_{result['doctor_name']}_{result['date']}.ics",
#                 mime="text/calendar"
#             )
        
#     if st.button("Go Back to Analysis"):
#         # Clean up all session state flags
#         del st.session_state.show_booking_form
#         del st.session_state.booking_success
#         if 'booking_result' in st.session_state:
#             del st.session_state.booking_result
#         if 'health_risks_for_booking' in st.session_state:
#             del st.session_state.health_risks_for_booking
#         st.rerun()
