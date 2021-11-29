<template>
    <div class='z2 fixed top right bottom left scroll-auto bg-darken50'>
        <div class='flex-parent flex-parent--center-main pt36'>
            <div class='flex-child bg-white round relative w600'>
                <button @click='$emit("err", false)' class='absolute top right px12 py12'>
                    <svg class='icon link color-darken50'><use xlink:href='#icon-close'></use></svg>
                </button>

                <div class='flex-parent flex-parent--center-main'>
                    <div class='flex-child pt12'>
                        <svg class='icon h60 w60 color-gray'><use href='#icon-alert'/></svg>
                    </div>
                </div>

                <div class='txt-l mb12 align-center'>Uh Oh!</div>
                <div class='txt-m align-center' v-text='err.message'></div>

                <button @click='$emit("err", false)' class='fr mb12 mr12 btn round btn--gray btn--stroke'>Ok</button>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'Err',
    props: ['err']
}
</script>
