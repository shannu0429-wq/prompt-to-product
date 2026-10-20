/**
 * Dynamic Team Member Manager for Prompt to Product Registration
 */

document.addEventListener('DOMContentLoaded', () => {
    const memberContainer = document.getElementById('additional-members-container');
    const addMemberBtn = document.getElementById('add-member-btn');
    const teamSizeSelect = document.getElementById('team_size');
    const memberCountBadge = document.getElementById('current-member-count');

    const MAX_MEMBERS = 4;
    let currentMembers = 1; // Leader is member 1

    function updateUI() {
        if (teamSizeSelect) {
            teamSizeSelect.value = currentMembers;
        }
        if (memberCountBadge) {
            memberCountBadge.textContent = `${currentMembers} / ${MAX_MEMBERS} Members`;
        }
        if (addMemberBtn) {
            if (currentMembers >= MAX_MEMBERS) {
                addMemberBtn.style.display = 'none';
            } else {
                addMemberBtn.style.display = 'inline-flex';
            }
        }
    }

    function createMemberCard(index) {
        const div = document.createElement('div');
        div.className = 'card member-card';
        div.id = `member-card-${index}`;
        div.style.marginBottom = '1.25rem';
        div.style.borderLeft = '3px solid #3b82f6';
        div.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: #38bdf8; font-size: 1.05rem;">
                    Team Member #${index + 1}
                </h4>
                <button type="button" class="btn btn-sm btn-danger remove-member-btn" data-index="${index}">
                    Remove
                </button>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Full Name <span class="required">*</span></label>
                    <input type="text" name="member_${index}_name" class="form-control" placeholder="Member full name" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Email Address <span class="required">*</span></label>
                    <input type="email" name="member_${index}_email" class="form-control" placeholder="member@college.edu" required>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Mobile Number (10 Digits) <span class="required">*</span></label>
                    <input type="tel" name="member_${index}_phone" class="form-control" placeholder="e.g. 9876543210" pattern="[6-9][0-9]{9}" required>
                </div>
                <div class="form-group">
                    <label class="form-label">College or Organization <span class="required">*</span></label>
                    <input type="text" name="member_${index}_college" class="form-control" placeholder="College or institute name" required>
                </div>
            </div>
        `;

        const removeBtn = div.querySelector('.remove-member-btn');
        removeBtn.addEventListener('click', () => {
            div.remove();
            currentMembers--;
            renumberMembers();
            updateUI();
        });

        return div;
    }

    function renumberMembers() {
        if (!memberContainer) return;
        const cards = memberContainer.querySelectorAll('.member-card');
        cards.forEach((card, idx) => {
            const memberNum = idx + 1; // 1-based index for additional member (member_1 is Member #2)
            card.id = `member-card-${memberNum}`;
            const title = card.querySelector('h4');
            if (title) title.textContent = `Team Member #${memberNum + 1}`;
            
            card.querySelector('input[name^="member_"][name$="_name"]').name = `member_${memberNum}_name`;
            card.querySelector('input[name^="member_"][name$="_email"]').name = `member_${memberNum}_email`;
            card.querySelector('input[name^="member_"][name$="_phone"]').name = `member_${memberNum}_phone`;
            card.querySelector('input[name^="member_"][name$="_college"]').name = `member_${memberNum}_college`;
        });
    }

    if (addMemberBtn && memberContainer) {
        addMemberBtn.addEventListener('click', () => {
            if (currentMembers < MAX_MEMBERS) {
                const card = createMemberCard(currentMembers);
                memberContainer.appendChild(card);
                currentMembers++;
                updateUI();
            }
        });
    }

    // Initialize UI
    updateUI();
});
