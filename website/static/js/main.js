// Initialize Owl Carousel
$(document).ready(function() {
    // Sample book data
    const books = [
        {
            title: "The Midnight Library",
            author: "Matt Haig",
            price: 24.99,
            image: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?ixlib=rb-4.0.3",
            rating: 5
        },
        {
            title: "The Silent Patient",
            author: "Alex Michaelides",
            price: 19.99,
            image: "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?ixlib=rb-4.0.3",
            rating: 4
        },
        {
            title: "Dune",
            author: "Frank Herbert",
            price: 29.99,
            image: "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?ixlib=rb-4.0.3",
            rating: 5
        },
        // Add more books as needed
    ];

    // Generate book cards and add them to the carousel
    const carousel = $('.owl-carousel');
    books.forEach(book => {
        const stars = '★'.repeat(book.rating) + '☆'.repeat(5 - book.rating);
        const bookCard = `
            <div class="book-card">
                <img src="${book.image}" alt="${book.title}">
                <div class="content">
                    <h4>${book.title}</h4>
                    <p class="text-muted">${book.author}</p>
                    <div class="rating">${stars}</div>
                    <div class="d-flex justify-content-between align-items-center mt-3">
                        <span class="price">$${book.price}</span>
                        <button class="btn btn-primary btn-sm add-to-cart">
                            <i class="fas fa-shopping-cart mr-1"></i> Add to Cart
                        </button>
                    </div>
                </div>
            </div>
        `;
        carousel.append(bookCard);
    });

    // Initialize Owl Carousel with custom options
    carousel.owlCarousel({
        loop: true,
        margin: 20,
        nav: true,
        dots: false,
        navText: [
            '<i class="fas fa-chevron-left"></i>',
            '<i class="fas fa-chevron-right"></i>'
        ],
        responsive: {
            0: {
                items: 1
            },
            600: {
                items: 2
            },
            1000: {
                items: 4
            }
        }
    });

    // Smooth scroll for navigation links
    $('a[href^="#"]').on('click', function(e) {
        e.preventDefault();
        const target = $(this.getAttribute('href'));
        if(target.length) {
            $('html, body').animate({
                scrollTop: target.offset().top - 80
            }, 1000);
        }
    });

    // Add to cart functionality
    let cartCount = 3; // Initial cart count
    $('.add-to-cart').on('click', function() {
        cartCount++;
        $('.badge').text(cartCount);
        
        // Add animation to cart icon
        const badge = $('.badge');
        badge.addClass('fade-in');
        setTimeout(() => badge.removeClass('fade-in'), 500);
        
        // Show success message
        const book = $(this).closest('.book-card');
        const title = book.find('h4').text();
        showNotification(`${title} added to cart!`);
    });

    // Notification function
    function showNotification(message) {
        const notification = $(`
            <div class="alert alert-success fade-in" 
                 style="position: fixed; top: 20px; right: 20px; z-index: 1000;">
                ${message}
            </div>
        `);
        
        $('body').append(notification);
        setTimeout(() => {
            notification.fadeOut(500, function() {
                $(this).remove();
            });
        }, 3000);
    }

    // Search functionality
    $('.form-control[placeholder="Search for books..."]').on('input', function() {
        const searchTerm = $(this).val().toLowerCase();
        $('.book-card').each(function() {
            const title = $(this).find('h4').text().toLowerCase();
            const author = $(this).find('p').text().toLowerCase();
            const visible = title.includes(searchTerm) || author.includes(searchTerm);
            $(this).toggle(visible);
        });
    });
});