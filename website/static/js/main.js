// Initialize all functionality when document is ready
$(document).ready(function() {
    const csrfToken = $('meta[name="csrf-token"]').attr('content');

    // Get shop items from existing cards
    const shopItems = $('.shop-items .card').map(function() {
        const card = $(this);
        return {
            id: card.data('id'),
            title: card.find('.card-title').text(),
            author: card.find('.card-text').text(),
            price: parseFloat(card.find('.fw-bold').text().replace('$', '')),
            image: card.find('.card-img-top').attr('src'),
            rating: card.find('.fa-star').length,
            inStock: !card.find('button').hasClass('disabled')
        };
    }).get();
    
    console.log(shopItems);
    const carousel = $('.owl-carousel');
    shopItems.forEach(book => {
        const stars = '★'.repeat(book.rating) + '☆'.repeat(5 - book.rating);
        const disabledClass = !book.inStock ? 'disabled' : ''; // Handle inStock dynamically
        
        const bookCard = `
            <div class="book-card">
                <img src="${book.image}" alt="Cover of ${book.title}" class="img-fluid">
                <div class="content">
                    <h4>${book.title}</h4>
                    <p class="text-muted">${book.author}</p>
                    <div class="rating">${stars}</div>
                    <div class="d-flex justify-content-between align-items-center mt-3">
                        <span class="price">$${book.price.toFixed(2)}</span>
                        <a href="/add-to-cart/${book.id}" 
                           class="btn btn-primary w-100 mt-3 ${disabledClass}" 
                           ${!book.inStock ? 'aria-disabled="true" tabindex="-1"' : ''}>
                            <i class="fas fa-shopping-cart me-2"></i>Add to Cart
                        </a>
                    </div>
                </div>
            </div>
        `;
        carousel.append(bookCard);
    });
    


    // Initialize Owl Carousel with custom options
    carousel.owlCarousel({
        loop: false,
        margin: 20,
        nav: true,
        dots: false,
        navText: [
            '<i class="fas fa-chevron-left"></i>',
            '<i class="fas fa-chevron-right"></i>'
        ],
        responsive: {
            0: { items: 1 },
            600: { items: 2 },
            1000: { items: 4 }
        },
        autoplay: true,
        autoplayTimeout: 5000,
        autoplayHoverPause: true
    });

    // Cart Functionality

    // Handle adding items to cart
    $('.add-to-cart').on('click', function (e) {
        e.preventDefault();
        const url = $(this).data('url');
        if (!url) {
            showNotification('Invalid URL. Failed to add item to cart.', 'danger');
            return;
        }

        $.ajax({
            url: url,
            type: 'POST',
            headers: { 'X-CSRFToken': csrfToken },
            success: function (response) {
                showNotification('Item added to cart successfully!', 'success');
                updateCartBadge(1);
            },
            error: function () {
                showNotification('Failed to add item to cart.', 'danger');
            },
        });
    });

    // Handle increasing quantity in cart
    $('.plus-cart').click(function () {
        const productId = $(this).attr('pid');
        const quantityElement = $(this).siblings('#quantity');
        const productQuantityElement = $(`#quantity${productId}`);

        $.ajax({
            url: '/pluscart',
            type: 'POST',
            headers: { 'X-CSRFToken': csrfToken },
            data: { cart_id: productId },
            success: function (response) {
                quantityElement.text(response.quantity);
                productQuantityElement.text(response.quantity);
                $('#amount_tt').text(response.amount.toFixed(2));
                $('#totalamount').text(response.total.toFixed(2));
                updateCartBadge(1);
            },
            error: function () {
                showNotification('Failed to update quantity', 'danger');
            },
        });
    });

    // Handle decreasing quantity in cart
    $('.minus-cart').click(function () {
        const productId = $(this).attr('pid');
        const quantityElement = $(this).siblings('#quantity');
        const productQuantityElement = $(`#quantity${productId}`);

        if (parseInt(quantityElement.text()) > 1) {
            $.ajax({
                url: '/minuscart',
                type: 'POST',
                headers: { 'X-CSRFToken': csrfToken },
                data: { cart_id: productId },
                success: function (response) {
                    quantityElement.text(response.quantity);
                    productQuantityElement.text(response.quantity);
                    $('#amount_tt').text(response.amount.toFixed(2));
                    $('#totalamount').text(response.total.toFixed(2));
                    updateCartBadge(-1);
                },
                error: function () {
                    showNotification('Failed to update quantity', 'danger');
                },
            });
        }
    });

    // Handle removing items from cart
    $('.remove-cart').click(function (e) {
        e.preventDefault();
        const productId = $(this).attr('pid');
        const productRow = $(this).closest('.row');

        $.ajax({
            url: '/removecart',
            type: 'POST',
            headers: { 'X-CSRFToken': csrfToken },
            data: { cart_id: productId },
            success: function (response) {
                productRow.fadeOut(300, function () {
                    $(this).remove();
                    $('#amount_tt').text(response.amount.toFixed(2));
                    $('#totalamount').text(response.total.toFixed(2));

                    // Check if cart is empty after removal
                    if ($('.card-body .row').length === 0) {
                        location.reload();
                    }
                });
                showNotification('Item removed from cart', 'success');
                updateCartBadge(-response.quantity);
            },
            error: function () {
                showNotification('Failed to remove item', 'danger');
            },
        });
    });

    // Update cart badge counter
    function updateCartBadge(change) {
        let badge = $('.cart-badge');
        if (badge.length === 0) {
            $('.nav-link.cart').append('<span class="badge bg-danger cart-badge">0</span>');
            badge = $('.cart-badge');
        }
        let count = parseInt(badge.text() || '0');
        count += change;
        badge.text(count);
        
        if (count <= 0) {
            badge.hide();
        } else {
            badge.show();
        }
    }

    // Show notification messages
    function showNotification(message, type = 'success') {
        const notification = $(`
            <div class="alert alert-${type} notification fade show" 
                 style="position: fixed; top: 20px; right: 20px; z-index: 1000;">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `);
        
        $('body').append(notification);
        
        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            notification.fadeOut(500, function() {
                $(this).remove();
            });
        }, 3000);
    }

    // Search functionality
    $('.search-input').on('input', function() {
        const searchTerm = $(this).val().toLowerCase();
        $('.book-card, .card').each(function() {
            const title = $(this).find('h4, .card-title').text().toLowerCase();
            const author = $(this).find('p, .card-text').text().toLowerCase();
            const visible = title.includes(searchTerm) || author.includes(searchTerm);
            $(this).closest('.col-md-3, .book-card').toggle(visible);
        });
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
});

document.addEventListener('DOMContentLoaded', function() {
    // Sidebar toggle functionality
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar, .admin-sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show-sidebar');
        });
    }

    // Admin nav active state
    if (document.querySelector('.admin-sidebar')) {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.admin-nav-item');
        
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }
});
