function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    const sidebarLinks = document.getElementById('sidebar-links');

    if (sidebar.style.left === "-200px") {
        sidebar.style.left = "0";
        content.style.marginLeft = "200px";
        sidebarLinks.style.opacity = 1;
    } else {
        sidebar.style.left = "-200px";
        content.style.marginLeft = "0";
        sidebarLinks.style.opacity = 0;
    }
}
