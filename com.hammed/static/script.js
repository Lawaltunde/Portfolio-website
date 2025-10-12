//


/*------------------------------------- Navigation parameters -------------------------------------*/

document.querySelector('.nav-button .Open').addEventListener('click',()=>{
    document.querySelector('nav .nav-container ul').style.left = '0';
    document.querySelector('.nav-button .Close').style.display='block'
    document.querySelector('.nav-button .Open').style.display='none'
});

document.querySelector('.nav-button .Close').addEventListener('click',()=>{
    document.querySelector('.nav-button .Close').style.display='none'
    document.querySelector('nav .nav-container ul').style.left = '-16rem';
    document.querySelector('.nav-button .Open').style.display='block'
})


/*------------------------------------- Active navigation -------------------------------------*/

const active = document.querySelectorAll('.nav-container ul li a');

active.forEach(index => {
    index.addEventListener('click',()=>{
        removeItem();
        index.classList.add('nav-active')
    })
});

function removeItem(){
    active.forEach(index => {
        index.classList.remove('nav-active');
    });
}

/*------------------------------------- About me section navigation -------------------------------------*/

// Get all elements with class 'tab_links'
let tablinks = document.getElementsByClassName('tab_links');

// Get all elements with class 'tab_content'
let tabcontents = document.getElementsByClassName('tab_content');

// Function that opens a tab with the given name
function opentab(tabname, evt){
    // Remove the 'active_link' class from all 'tab_links'
    for (let tablink of tablinks){
        if (tablink && tablink.classList) {
            tablink.classList.remove('active_link');
        }
    }

    // Remove the 'active_tab' class from all 'tab_content'
    for (let tabcontent of tabcontents){
        if (tabcontent && tabcontent.classList) {
            tabcontent.classList.remove('active_tab');
        }
    }

    // Add the 'active_link' class to the clicked 'tab_link'
    if (evt && evt.currentTarget && evt.currentTarget.classList) {
        evt.currentTarget.classList.add('active_link');
    }

    // Add the 'active_tab' class to the content element with the given 'tabname'
    const contentEl = document.getElementById(tabname);
    if (contentEl && contentEl.classList) {
        contentEl.classList.add('active_tab');
    }
}


/*------------------------------------- About me section navigation -------------------------------------*/

// ScrollReveal({
//     reset: true,
//     distance: '80px',
//     duration: 2000,
//     delay: 200
// });

// ScrollReveal().reveal('.contact_text', { origin: 'top' });
// ScrollReveal().reveal('.home_img, .portfolio_container, .contact form', { origin: 'bottom' });
// ScrollReveal().reveal('.home_content h1, .about_img', { origin: 'left' });
// ScrollReveal().reveal('.home_content p, .abount_info', { origin: 'right' });


/*------------------------------------- Typed JS -------------------------------------*/
(function initTypedBanner(){
    const target = document.querySelector('.multiple_text');
    const hasTyped = (typeof window !== 'undefined' && typeof window.Typed === 'function');
    if (!target || !hasTyped) {
        // Element missing or Typed.js not loaded; skip initialization
        return;
    }
    try {
        new window.Typed(target, {
            strings: ['Software Engineer', 'Full Stack Developer'],
            typeSpeed: 100,
            backSpeed: 100,
            backDelay: 1000,
            loop: true
        });
    } catch (err) {
        if (typeof console !== 'undefined' && console.error) {
            console.error('Typed initialization failed:', err);
        }
    }
})();
