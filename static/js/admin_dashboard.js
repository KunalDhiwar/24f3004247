/* ==========================================================
            ADMIN DASHBOARD JAVASCRIPT
   ========================================================== */
/*
    Profile Dropdown
*/
const profileBtn = document.getElementById("profileBtn");
const profileDropdown = document.getElementById("profileDropdown");

if(profileBtn && profileDropdown){

    // Open / Close Dropdown
    profileBtn.addEventListener("click", function(event){
        event.stopPropagation();
        profileDropdown.classList.toggle("show");
        profileBtn.classList.toggle("active");
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", function(event){
        if(
            !profileDropdown.contains(event.target) &&
            !profileBtn.contains(event.target)
        ){
            profileDropdown.classList.remove("show");
            profileBtn.classList.remove("active");
        }
    });

    // Prevent dropdown close when clicking inside
    profileDropdown.addEventListener("click", function(event){
        event.stopPropagation();
    });
}